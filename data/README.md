# Data Directory

This directory contains the application's persistent data.

## Contents

- **dndgame.db** - SQLite database file storing all game data
  - Players
  - Sessions
  - Characters
  - Messages
  - Session-player relationships

## Database

The database is automatically created when the application first runs. It uses SQLite for development and can be configured to use PostgreSQL for production via the `DATABASE_URL` environment variable.

### Default Location
```
data/dndgame.db
```

### Configuration
Set in `.env` file:
```bash
DATABASE_URL=sqlite:///./data/dndgame.db
```

### Backup
To backup your database:
```bash
cp data/dndgame.db data/dndgame.db.backup
```

### Reset Database
To start fresh (WARNING: This deletes all data):
```bash
rm data/dndgame.db
# Database will be recreated on next application start
```

## Git Ignore

The database file is ignored by git (see `.gitignore`) to prevent accidentally committing sensitive game data. Only the `.gitkeep` file is tracked to ensure this directory structure exists in the repository.
