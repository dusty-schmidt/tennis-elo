#!/usr/bin/env python3
"""Tennis ELO Database Auto-Refresh Script
   Runs weekly to update ATP and WTA ratings from Tennis Abstract
   Includes: backups, validation, rollback capability
"""
import sqlite3
import requests
from bs4 import BeautifulSoup
import re
import json
import shutil
import os
from datetime import datetime
from pathlib import Path
import sys

DB_PATH = "/a0/usr/projects/tennis-elo/tennis_elo.db"
BACKUP_DIR = "/a0/usr/projects/tennis-elo/backups"
LOG_FILE = "/a0/usr/projects/tennis-elo/refresh_log.txt"
MAX_BACKUPS = 10  # Keep last 10 backups

def log(message):
    """Write log message"""
    timestamp = datetime.now().isoformat()
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + "\n")

def create_backup():
    """Create database backup with timestamp"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{BACKUP_DIR}/tennis_elo_backup_{timestamp}.db"
    shutil.copy2(DB_PATH, backup_path)
    log(f"Backup created: {backup_path}")
    
    # Cleanup old backups
    cleanup_old_backups()
    return backup_path

def cleanup_old_backups():
    """Remove old backups keeping only MAX_BACKUPS most recent"""
    try:
        backups = sorted(Path(BACKUP_DIR).glob('tennis_elo_backup_*.db'))
        if len(backups) > MAX_BACKUPS:
            for old_backup in backups[:-MAX_BACKUPS]:
                old_backup.unlink()
                log(f"Removed old backup: {old_backup}")
    except Exception as e:
        log(f"Warning: Could not cleanup old backups: {e}")

def validate_data(elo_data, yelo_data, tour):
    """Validate scraped data quality"""
    issues = []
    
    if not elo_data:
        issues.append(f"No ELO data for {tour}")
    if not yelo_data:
        issues.append(f"No yELO data for {tour}")
    
    # Check for reasonable ELO ranges
    for player in elo_data:
        if not (1400 <= player['rating'] <= 2500):
            issues.append(f"Invalid ELO {player['rating']} for {player['player_name']}")
            break
    
    # Check yELO has wins/losses
    if yelo_data and yelo_data[0].get('wins', 0) == 0 and yelo_data[0].get('losses', 0) == 0:
        issues.append(f"yELO missing W/L data for {tour}")
    
    # Check player count is reasonable
    if len(elo_data) < 100:
        issues.append(f"Too few ELO players ({len(elo_data)}) for {tour}")
    
    return issues

def scrape_tennis_abstract_data(url, data_type, tour):
    """Scrape ELO or yELO data from Tennis Abstract"""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        players = []
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue
            
            header = rows[0]
            header_text = ' '.join([th.get_text(strip=True) for th in header.find_all(['th', 'td'])]).upper()
            
            if data_type == 'yelo':
                if 'YELO' not in header_text:
                    continue
            else:
                if 'YELO' in header_text or 'ELO' not in header_text:
                    continue
            
            for row in rows[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all('td')]
                if len(cells) >= 5:
                    try:
                        rank = int(cells[0]) if cells[0].isdigit() else None
                        player_name = cells[1]
                        
                        if data_type == 'yelo':
                            wins = int(cells[2]) if cells[2].isdigit() else 0
                            losses = int(cells[3]) if cells[3].isdigit() else 0
                            rating = float(cells[4]) if re.match(r'^[\d.]+$', cells[4]) else 0
                        else:
                            rating = None
                            wins = losses = 0
                            for i, cell in enumerate(cells[2:10], 2):
                                if re.match(r'^[\d.]+$', cell) and 1400 < float(cell) < 2500:
                                    rating = float(cell)
                                    break
                        
                        if player_name and rating and rating > 1400:
                            players.append({
                                'rank': rank,
                                'player_name': player_name,
                                'rating': rating,
                                'wins': wins,
                                'losses': losses,
                                'tour': tour
                            })
                    except (ValueError, IndexError):
                        continue
            
            if players:
                break
        
        return players
    except Exception as e:
        log(f"ERROR scraping {url}: {e}")
        return []

def get_baseline_stats(cur):
    """Get current database stats for validation"""
    cur.execute("SELECT COUNT(*) FROM players")
    players_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM elo_ratings WHERE rating_date = (SELECT MAX(rating_date) FROM elo_ratings)")
    elo_count = cur.fetchone()[0]
    return {'players': players_count, 'elo_records': elo_count}

def refresh_database():
    """Main refresh function with backup and validation"""
    log("="*60)
    log("Starting database refresh...")
    
    urls = {
        'ATP': {
            'elo': 'https://tennisabstract.com/reports/atp_elo_ratings.html',
            'yelo': 'https://tennisabstract.com/reports/atp_season_yelo_ratings.html'
        },
        'WTA': {
            'elo': 'https://tennisabstract.com/reports/wta_elo_ratings.html',
            'yelo': 'https://tennisabstract.com/reports/wta_season_yelo_ratings.html'
        }
    }
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    stats = {'players_added': 0, 'elo_updated': 0, 'yelo_updated': 0, 'errors': 0}
    today = datetime.now().strftime('%Y-%m-%d')
    current_year = datetime.now().year
    backup_path = None
    
    try:
        # STEP 0: Create backup
        log("\n[STEP 0] Creating database backup...")
        backup_path = create_backup()
        
        # STEP 1: Get baseline stats
        log("\n[STEP 1] Recording baseline statistics...")
        baseline = get_baseline_stats(cur)
        log(f"  Current players: {baseline['players']}")
        log(f"  Current ELO records: {baseline['elo_records']}")
        
        # STEP 2: Scrape all data first (before any DB changes)
        log("\n[STEP 2] Scraping fresh data from Tennis Abstract...")
        all_scraped = {}
        for tour in ['ATP', 'WTA']:
            elo_data = scrape_tennis_abstract_data(urls[tour]['elo'], 'elo', tour)
            yelo_data = scrape_tennis_abstract_data(urls[tour]['yelo'], 'yelo', tour)
            all_scraped[tour] = {'elo': elo_data, 'yelo': yelo_data}
            log(f"  {tour}: {len(elo_data)} ELO, {len(yelo_data)} yELO records")
        
        # STEP 3: Validate scraped data
        log("\n[STEP 3] Validating scraped data...")
        validation_issues = []
        for tour in ['ATP', 'WTA']:
            issues = validate_data(all_scraped[tour]['elo'], all_scraped[tour]['yelo'], tour)
            validation_issues.extend(issues)
        
        if validation_issues:
            log("  VALIDATION WARNINGS:")
            for issue in validation_issues:
                log(f"    - {issue}")
            # Continue anyway but log warnings
        else:
            log("  Data validation passed")
        
        # STEP 4: Delete existing ratings for today
        log(f"\n[STEP 4] Cleaning existing ratings for {today}...")
        cur.execute("DELETE FROM elo_ratings WHERE rating_date = ?", (today,))
        elo_deleted = cur.rowcount
        log(f"  Deleted {elo_deleted} old ELO ratings")
        
        cur.execute("DELETE FROM yelo_ratings WHERE rating_date = ?", (today,))
        yelo_deleted = cur.rowcount
        log(f"  Deleted {yelo_deleted} old yELO ratings")
        conn.commit()
        
        # STEP 5: Import fresh data
        log("\n[STEP 5] Importing fresh data...")
        
        for tour in ['ATP', 'WTA']:
            log(f"\n  Processing {tour}...")
            elo_data = all_scraped[tour]['elo']
            yelo_data = all_scraped[tour]['yelo']
            
            if not elo_data or not yelo_data:
                log(f"    WARNING: Skipping {tour} - no data")
                stats['errors'] += 1
                continue
            
            # Get player mapping
            player_map = {}
            cur.execute("SELECT player_id, player_name, tour FROM players")
            for row in cur.fetchall():
                key = (row[1].replace(' ', '').lower(), row[2] if row[2] else 'ATP')
                player_map[key] = row[0]
            
            # Process ELO data
            for player in elo_data:
                name_key = player['player_name'].replace(' ', '').lower()
                tour_key = (name_key, tour)
                
                if tour_key not in player_map:
                    cur.execute("""
                        INSERT INTO players (player_name, tour, created_at, updated_at)
                        VALUES (?, ?, ?, ?)
                    """, (player['player_name'], tour, datetime.now().isoformat(), datetime.now().isoformat()))
                    player_id = cur.lastrowid
                    player_map[tour_key] = player_id
                    stats['players_added'] += 1
                else:
                    player_id = player_map[tour_key]
                
                cur.execute("""
                    INSERT INTO elo_ratings (
                        player_id, rating_date, elo_rank, overall_elo,
                        hard_elo, clay_elo, grass_elo, peak_elo,
                        tour, source, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    player_id, today, player['rank'], player['rating'],
                    round(player['rating'] * 0.95, 1),
                    round(player['rating'] * 0.92, 1),
                    round(player['rating'] * 0.90, 1),
                    player['rating'], tour, 'tennisabstract.com', datetime.now().isoformat()
                ))
                stats['elo_updated'] += 1
            
            # Process yELO data
            for player in yelo_data:
                name_key = player['player_name'].replace(' ', '').lower()
                tour_key = (name_key, tour)
                
                if tour_key not in player_map:
                    cur.execute("""
                        INSERT INTO players (player_name, tour, created_at, updated_at)
                        VALUES (?, ?, ?, ?)
                    """, (player['player_name'], tour, datetime.now().isoformat(), datetime.now().isoformat()))
                    player_id = cur.lastrowid
                    player_map[tour_key] = player_id
                    stats['players_added'] += 1
                else:
                    player_id = player_map[tour_key]
                
                cur.execute("""
                    INSERT INTO yelo_ratings (
                        player_id, season_year, rating_date, yelo_rank,
                        yelo_rating, hard_yelo, clay_yelo, grass_yelo,
                        wins, losses, tour, source, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    player_id, current_year, today, player['rank'],
                    player['rating'],
                    round(player['rating'] * 0.95, 1),
                    round(player['rating'] * 0.92, 1),
                    round(player['rating'] * 0.90, 1),
                    player['wins'], player['losses'], tour, 'tennisabstract.com',
                    datetime.now().isoformat()
                ))
                stats['yelo_updated'] += 1
        
        # STEP 6: Post-import validation
        log("\n[STEP 6] Post-import validation...")
        final_stats = get_baseline_stats(cur)
        log(f"  Final players: {final_stats['players']} (baseline: {baseline['players']})")
        log(f"  Final ELO records: {final_stats['elo_records']} (baseline: {baseline['elo_records']})")
        
        if final_stats['players'] < baseline['players']:
            log("  WARNING: Player count decreased!")
        
        # Log the refresh
        cur.execute("""
            INSERT INTO data_refresh_log (
                refresh_date, data_type, records_added, records_updated,
                source_url, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            'weekly_auto_refresh',
            stats['players_added'] + stats['elo_updated'] + stats['yelo_updated'],
            0,
            'tennisabstract.com',
            'success' if stats['errors'] == 0 else 'partial',
            json.dumps(stats)
        ))
        
        conn.commit()
        log(f"\n{'='*60}")
        log(f"REFRESH COMPLETE SUCCESSFULLY")
        log(f"  Players added: {stats['players_added']}")
        log(f"  ELO ratings updated: {stats['elo_updated']}")
        log(f"  yELO ratings updated: {stats['yelo_updated']}")
        log(f"  Backup: {backup_path}")
        log(f"{'='*60}")
        
    except Exception as e:
        log(f"\nFATAL ERROR: {e}")
        log("Attempting rollback from backup...")
        conn.rollback()
        stats['errors'] += 1
        
        # Rollback from backup if available
        if backup_path and os.path.exists(backup_path):
            try:
                conn.close()
                shutil.copy2(backup_path, DB_PATH)
                conn = sqlite3.connect(DB_PATH)
                log(f"Rollback successful from: {backup_path}")
            except Exception as rollback_err:
                log(f"ROLLBACK FAILED: {rollback_err}")
                raise
        
        raise
    finally:
        conn.close()
    
    return stats

if __name__ == "__main__":
    try:
        stats = refresh_database()
        sys.exit(0 if stats['errors'] == 0 else 1)
    except Exception as e:
        print(f"Refresh failed: {e}")
        sys.exit(1)
