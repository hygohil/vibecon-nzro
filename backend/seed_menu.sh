#!/bin/bash
# Quick command to run all seeding utilities

echo "🌳 Aggregator OS - Database Seeding Utilities"
echo "=============================================="
echo ""
echo "Available commands:"
echo ""
echo "1. Seed database with test data"
echo "   → cd /app/backend && python3 seed_data.py"
echo ""
echo "2. View database statistics"
echo "   → cd /app/backend && python3 view_db_stats.py"
echo ""
echo "3. Validate seeded data"
echo "   → cd /app/backend && python3 validate_seed_data.py"
echo ""
echo "4. Clear all seed data"
echo "   → cd /app/backend && python3 clear_seed_data.py"
echo ""
echo "=============================================="
echo ""
read -p "Enter command number (1-4) or 'q' to quit: " choice

case $choice in
    1)
        echo ""
        cd /app/backend && python3 seed_data.py
        ;;
    2)
        echo ""
        cd /app/backend && python3 view_db_stats.py
        ;;
    3)
        echo ""
        cd /app/backend && python3 validate_seed_data.py
        ;;
    4)
        echo ""
        cd /app/backend && python3 clear_seed_data.py
        ;;
    q|Q)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
