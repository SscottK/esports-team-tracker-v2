# Development TODOs

## Features
- [ ] Add admin-only CSV level importer
  - Create view for uploading CSV files
  - Add CSV parser to handle level data
  - Validate and import levels for specific games
  - Show import results and any errors
  - Add success/error messages
- [ ] Add game icons to games list in team details page
  - Add icon field to Game model
  - Add icon upload in admin interface
  - Display icon next to game name in team details
- [ ] Add pagination to game suggestions list
- [ ] Add sorting options for game suggestions (by date, name, etc.)
- [ ] Add bulk actions for game suggestions (approve/delete multiple)
- [ ] Add email notifications for admins when new games are suggested
- [ ] Add search functionality to games dropdown when adding games to teams

## Improvements
- [ ] Optimize database queries for team details page
- [ ] Add loading states to forms and buttons
- [ ] Improve mobile responsiveness
- [ ] Add confirmation dialogs for important actions
- [ ] Add error boundaries for better error handling

## Bug Fixes
- [ ] Fix any styling inconsistencies across different browsers
- [ ] Address potential race conditions in game suggestion handling
- [ ] Ensure proper error handling for file uploads

## Technical Debt
- [ ] Add comprehensive test coverage
- [ ] Document API endpoints
- [ ] Refactor repeated code in views
- [ ] Update dependencies to latest stable versions
- [ ] Add type hints to Python code 