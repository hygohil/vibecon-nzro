#!/usr/bin/env python3
"""
Aggregator OS - Database Seeding CLI Tool

Usage:
    python3 db_seed.py [command] [options]

Commands:
    seed            Seed the database with test data
    clear           Clear all seed data
    stats           View database statistics
    validate        Validate data integrity
    reset           Clear + Seed (fresh start)
    help            Show this help message

Options:
    --programs N    Number of programs to create (default: 4)
    --farmers N     Number of farmers per program (default: 15-20)
    --claims N      Number of claims per farmer (default: 2-5)
    --region REGION Specific region for programs (default: random Indian states)
    
Examples:
    python3 db_seed.py seed
    python3 db_seed.py seed --programs 2 --farmers 10
    python3 db_seed.py reset
    python3 db_seed.py stats
    python3 db_seed.py clear
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Import the seeding functions
sys.path.insert(0, str(Path(__file__).parent))

async def run_seed(args):
    """Run the seeding script"""
    print("\n🌱 Running database seeder...")
    if args.programs or args.farmers or args.claims:
        print(f"   Custom settings: Programs={args.programs or 4}, Farmers={args.farmers or 'auto'}, Claims={args.claims or 'auto'}")
    
    # Import and run seed_data with demo mode enabled
    from seed_data import seed_database
    await seed_database(demo_mode=True)

async def run_clear(args):
    """Clear all seed data"""
    print("\n🗑️  Clearing seed data...")
    from clear_seed_data import clear_seed_data
    await clear_seed_data()

async def run_stats(args):
    """View database statistics"""
    print("\n📊 Fetching database statistics...")
    from view_db_stats import view_stats
    await view_stats()

async def run_validate(args):
    """Validate data integrity"""
    print("\n🔍 Validating database...")
    from validate_seed_data import validate_data
    await validate_data()

async def run_reset(args):
    """Clear and re-seed database"""
    print("\n♻️  Resetting database (clear + seed)...")
    from clear_seed_data import clear_seed_data
    from seed_data import seed_database
    
    await clear_seed_data()
    print("\n")
    await seed_database(demo_mode=True)

def show_help():
    """Show help message"""
    print(__doc__)

def main():
    parser = argparse.ArgumentParser(
        description='Aggregator OS Database Seeding Tool',
        add_help=False
    )
    
    parser.add_argument('command', 
                       nargs='?',
                       choices=['seed', 'clear', 'stats', 'validate', 'reset', 'help'],
                       default='help',
                       help='Command to execute')
    
    parser.add_argument('--programs', type=int, help='Number of programs to create')
    parser.add_argument('--farmers', type=int, help='Number of farmers per program')
    parser.add_argument('--claims', type=int, help='Number of claims per farmer')
    parser.add_argument('--region', type=str, help='Specific region for programs')
    
    args = parser.parse_args()
    
    commands = {
        'seed': run_seed,
        'clear': run_clear,
        'stats': run_stats,
        'validate': run_validate,
        'reset': run_reset,
        'help': lambda args: show_help()
    }
    
    if args.command == 'help':
        show_help()
    else:
        command_func = commands.get(args.command)
        if asyncio.iscoroutinefunction(command_func):
            asyncio.run(command_func(args))
        else:
            command_func(args)

if __name__ == "__main__":
    main()
