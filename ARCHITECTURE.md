# MQTT Explorer - Refactored Architecture

This project has been refactored into a modular architecture with separate classes for different responsibilities.

## File Structure

### Main.py
- Entry point of the application
- Creates the main window and initializes the frontend

### frontend.py - MQTTFrontend Class
**Responsibilities:**
- GUI creation and management
- User interface event handling
- Message display and UI updates
- Window management (main window, database viewer)
- User input validation

**Key Features:**
- Connection settings UI
- Subscribe/Publish controls
- Message display with autoscroll
- Database viewer window
- Export functionality UI

### backend.py - MQTTBackend Class
**Responsibilities:**
- MQTT client operations
- Connection management
- Message publishing/subscribing
- File I/O for storing connection history
- MQTT event callbacks

**Key Features:**
- MQTT broker connection handling
- Topic subscription management
- Message publishing
- Connection state management
- Storage of brokers, ports, and topics

### database.py - MQTTDatabase Class
**Responsibilities:**
- SQLite database operations
- Message storage and retrieval
- Database maintenance
- Data export functionality

**Key Features:**
- Message persistence
- Database querying
- JSON export
- Thread-safe operations

## Architecture Benefits

1. **Separation of Concerns**: Each class has a single, well-defined responsibility
2. **Maintainability**: Changes to one component don't affect others
3. **Testability**: Each class can be tested independently
4. **Reusability**: Components can be reused in other projects
5. **Scalability**: Easy to add new features to specific components

## Usage

Run the application with:
```bash
python Main.py
```

All functionality remains the same as the original monolithic version, but the code is now much more organized and maintainable.
