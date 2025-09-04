"""
Command Pattern Implementation for Bartr
Handles encapsulation of operations as objects for undo/redo, queuing, and logging
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import json
from bartr.models import malaysia_now


class CommandStatus(Enum):
    """Status of command execution"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNDONE = "undone"


class Command(ABC):
    """Abstract base class for all commands"""
    
    def __init__(self, description: str = None):
        self.description = description or self.__class__.__name__
        self.status = CommandStatus.PENDING
        self.executed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
    
    @abstractmethod
    def execute(self) -> bool:
        """Execute the command"""
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        """Undo the command"""
        pass
    
    @abstractmethod
    def can_undo(self) -> bool:
        """Check if command can be undone"""
        pass
    
    def get_status(self) -> CommandStatus:
        """Get command status"""
        return self.status
    
    def set_metadata(self, key: str, value: Any):
        """Set metadata for the command"""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default=None):
        """Get metadata value"""
        return self.metadata.get(key, default)


class SuspendUserCommand(Command):
    """Command to suspend a user"""
    
    def __init__(self, user_id: int, admin_id: int, reason: str, duration_days: int = None):
        super().__init__(f"Suspend user {user_id}")
        self.user_id = user_id
        self.admin_id = admin_id
        self.reason = reason
        self.duration_days = duration_days
        self._original_status = None
    
    def execute(self) -> bool:
        """Execute user suspension"""
        try:
            from bartr.models import User
            from bartr import db
            from bartr.patterns.observer import event_manager, EventType
            
            self.status = CommandStatus.EXECUTING
            
            user = User.query.get(self.user_id)
            if not user:
                self.status = CommandStatus.FAILED
                self.error_message = "User not found"
                return False
            
            # Store original status for undo
            self._original_status = user.is_active
            
            # Suspend user
            user.is_active = False
            user.suspended_at = malaysia_now()
            user.suspended_by = self.admin_id
            user.suspension_reason = self.reason
            
            if self.duration_days:
                from datetime import timedelta
                user.suspension_expires = malaysia_now() + timedelta(days=self.duration_days)
            
            db.session.commit()
            
            # Emit event
            event_manager.emit_user_suspended(
                user_id=self.user_id,
                admin_id=self.admin_id,
                reason=self.reason
            )
            
            self.status = CommandStatus.COMPLETED
            self.executed_at = malaysia_now()
            return True
            
        except Exception as e:
            self.status = CommandStatus.FAILED
            self.error_message = str(e)
            return False
    
    def undo(self) -> bool:
        """Undo user suspension"""
        try:
            from bartr.models import User
            from bartr import db
            
            user = User.query.get(self.user_id)
            if not user:
                return False
            
            # Restore original status
            user.is_active = self._original_status
            user.suspended_at = None
            user.suspended_by = None
            user.suspension_reason = None
            user.suspension_expires = None
            
            db.session.commit()
            
            self.status = CommandStatus.UNDONE
            return True
            
        except Exception as e:
            self.error_message = f"Undo failed: {str(e)}"
            return False
    
    def can_undo(self) -> bool:
        """Check if suspension can be undone"""
        return (self.status == CommandStatus.COMPLETED and 
                self._original_status is not None)


class DeleteItemCommand(Command):
    """Command to delete an item"""
    
    def __init__(self, item_id: int, admin_id: int, reason: str = None):
        super().__init__(f"Delete item {item_id}")
        self.item_id = item_id
        self.admin_id = admin_id
        self.reason = reason
        self._item_backup = None
    
    def execute(self) -> bool:
        """Execute item deletion"""
        try:
            from bartr.models import Item
            from bartr import db
            from bartr.patterns.observer import event_manager, EventType
            
            self.status = CommandStatus.EXECUTING
            
            item = Item.query.get(self.item_id)
            if not item:
                self.status = CommandStatus.FAILED
                self.error_message = "Item not found"
                return False
            
            # Create backup for undo
            self._item_backup = {
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'category_id': item.category_id,
                'condition': item.condition,
                'estimated_value': item.estimated_value,
                'user_id': item.user_id,
                'is_active': item.is_active,
                'created_at': item.created_at,
                'image_urls': item.image_urls
            }
            
            # Emit event before deletion
            event_manager.emit_item_deleted(
                item_id=item.id,
                item_name=item.name,
                user_id=item.user_id,
                admin_id=self.admin_id
            )
            
            # Soft delete - mark as inactive
            item.is_active = False
            item.deleted_at = malaysia_now()
            item.deleted_by = self.admin_id
            item.deletion_reason = self.reason
            
            db.session.commit()
            
            self.status = CommandStatus.COMPLETED
            self.executed_at = malaysia_now()
            return True
            
        except Exception as e:
            self.status = CommandStatus.FAILED
            self.error_message = str(e)
            return False
    
    def undo(self) -> bool:
        """Undo item deletion"""
        try:
            from bartr.models import Item
            from bartr import db
            
            if not self._item_backup:
                return False
            
            item = Item.query.get(self.item_id)
            if not item:
                return False
            
            # Restore item
            item.is_active = True
            item.deleted_at = None
            item.deleted_by = None
            item.deletion_reason = None
            
            db.session.commit()
            
            self.status = CommandStatus.UNDONE
            return True
            
        except Exception as e:
            self.error_message = f"Undo failed: {str(e)}"
            return False
    
    def can_undo(self) -> bool:
        """Check if deletion can be undone"""
        return (self.status == CommandStatus.COMPLETED and 
                self._item_backup is not None)


class CreateBackupCommand(Command):
    """Command to create a database backup"""
    
    def __init__(self, filename: str = None):
        super().__init__("Create database backup")
        self.filename = filename
        self._backup_path = None
    
    def execute(self) -> bool:
        """Execute backup creation"""
        try:
            from bartr.admin.routes import create_sql_backup
            import os
            from datetime import datetime
            
            self.status = CommandStatus.EXECUTING
            
            if not self.filename:
                timestamp = malaysia_now().strftime('%Y%m%d_%H%M%S')
                self.filename = f"backup_{timestamp}.sql"
            
            # Create backup
            backup_content = create_sql_backup()
            
            # Save to file
            backup_dir = 'backups'
            os.makedirs(backup_dir, exist_ok=True)
            
            self._backup_path = os.path.join(backup_dir, self.filename)
            
            with open(self._backup_path, 'w') as f:
                f.write(backup_content)
            
            self.set_metadata('backup_path', self._backup_path)
            self.set_metadata('file_size', os.path.getsize(self._backup_path))
            
            self.status = CommandStatus.COMPLETED
            self.executed_at = malaysia_now()
            return True
            
        except Exception as e:
            self.status = CommandStatus.FAILED
            self.error_message = str(e)
            return False
    
    def undo(self) -> bool:
        """Undo backup creation (delete backup file)"""
        try:
            import os
            
            if self._backup_path and os.path.exists(self._backup_path):
                os.remove(self._backup_path)
                self.status = CommandStatus.UNDONE
                return True
            
            return False
            
        except Exception as e:
            self.error_message = f"Undo failed: {str(e)}"
            return False
    
    def can_undo(self) -> bool:
        """Check if backup creation can be undone"""
        return (self.status == CommandStatus.COMPLETED and 
                self._backup_path is not None)


class BatchCommand(Command):
    """Command that executes multiple commands as a batch"""
    
    def __init__(self, commands: List[Command], description: str = None):
        super().__init__(description or "Batch operation")
        self.commands = commands
        self.executed_commands: List[Command] = []
    
    def execute(self) -> bool:
        """Execute all commands in batch"""
        try:
            self.status = CommandStatus.EXECUTING
            
            for command in self.commands:
                if command.execute():
                    self.executed_commands.append(command)
                else:
                    # If any command fails, undo all executed commands
                    self._rollback()
                    self.status = CommandStatus.FAILED
                    self.error_message = f"Batch failed at command: {command.description}"
                    return False
            
            self.status = CommandStatus.COMPLETED
            self.executed_at = malaysia_now()
            return True
            
        except Exception as e:
            self._rollback()
            self.status = CommandStatus.FAILED
            self.error_message = str(e)
            return False
    
    def undo(self) -> bool:
        """Undo all commands in reverse order"""
        try:
            success = True
            
            # Undo in reverse order
            for command in reversed(self.executed_commands):
                if command.can_undo():
                    if not command.undo():
                        success = False
            
            if success:
                self.status = CommandStatus.UNDONE
            
            return success
            
        except Exception as e:
            self.error_message = f"Undo failed: {str(e)}"
            return False
    
    def can_undo(self) -> bool:
        """Check if batch can be undone"""
        return (self.status == CommandStatus.COMPLETED and 
                all(cmd.can_undo() for cmd in self.executed_commands))
    
    def _rollback(self):
        """Rollback executed commands on failure"""
        for command in reversed(self.executed_commands):
            if command.can_undo():
                command.undo()


class MacroCommand(Command):
    """Command that records and replays a sequence of commands"""
    
    def __init__(self, name: str):
        super().__init__(f"Macro: {name}")
        self.name = name
        self.recorded_commands: List[Dict[str, Any]] = []
        self.is_recording = False
    
    def start_recording(self):
        """Start recording commands"""
        self.is_recording = True
        self.recorded_commands.clear()
    
    def stop_recording(self):
        """Stop recording commands"""
        self.is_recording = False
    
    def record_command(self, command_type: str, params: Dict[str, Any]):
        """Record a command during recording"""
        if self.is_recording:
            self.recorded_commands.append({
                'type': command_type,
                'params': params,
                'timestamp': malaysia_now().isoformat()
            })
    
    def execute(self) -> bool:
        """Execute recorded macro"""
        try:
            self.status = CommandStatus.EXECUTING
            
            for recorded_cmd in self.recorded_commands:
                command = self._create_command_from_record(recorded_cmd)
                if command and not command.execute():
                    self.status = CommandStatus.FAILED
                    self.error_message = f"Macro failed at: {recorded_cmd['type']}"
                    return False
            
            self.status = CommandStatus.COMPLETED
            self.executed_at = malaysia_now()
            return True
            
        except Exception as e:
            self.status = CommandStatus.FAILED
            self.error_message = str(e)
            return False
    
    def undo(self) -> bool:
        """Undo is not supported for macros"""
        return False
    
    def can_undo(self) -> bool:
        """Macros cannot be undone"""
        return False
    
    def save_to_file(self, filepath: str):
        """Save macro to file"""
        try:
            macro_data = {
                'name': self.name,
                'description': self.description,
                'commands': self.recorded_commands,
                'created_at': malaysia_now().isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(macro_data, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def load_from_file(self, filepath: str):
        """Load macro from file"""
        try:
            with open(filepath, 'r') as f:
                macro_data = json.load(f)
            
            self.name = macro_data['name']
            self.description = macro_data['description']
            self.recorded_commands = macro_data['commands']
            
            return True
        except Exception:
            return False
    
    def _create_command_from_record(self, record: Dict[str, Any]) -> Optional[Command]:
        """Create command object from recorded data"""
        command_type = record['type']
        params = record['params']
        
        if command_type == 'suspend_user':
            return SuspendUserCommand(**params)
        elif command_type == 'delete_item':
            return DeleteItemCommand(**params)
        elif command_type == 'create_backup':
            return CreateBackupCommand(**params)
        
        return None


class CommandInvoker:
    """Invoker that executes and manages commands"""
    
    def __init__(self):
        self.command_history: List[Command] = []
        self.current_position = -1
        self.max_history = 100
    
    def execute_command(self, command: Command) -> bool:
        """Execute a command and add to history"""
        success = command.execute()
        
        if success:
            # Remove any commands after current position (for redo)
            self.command_history = self.command_history[:self.current_position + 1]
            
            # Add command to history
            self.command_history.append(command)
            self.current_position += 1
            
            # Limit history size
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)
                self.current_position -= 1
        
        return success
    
    def undo(self) -> bool:
        """Undo the last command"""
        if self.current_position >= 0:
            command = self.command_history[self.current_position]
            if command.can_undo() and command.undo():
                self.current_position -= 1
                return True
        
        return False
    
    def redo(self) -> bool:
        """Redo the next command"""
        if self.current_position < len(self.command_history) - 1:
            self.current_position += 1
            command = self.command_history[self.current_position]
            return command.execute()
        
        return False
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return (self.current_position >= 0 and 
                self.command_history[self.current_position].can_undo())
    
    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return self.current_position < len(self.command_history) - 1
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get command history"""
        return [
            {
                'description': cmd.description,
                'status': cmd.status.value,
                'executed_at': cmd.executed_at.isoformat() if cmd.executed_at else None,
                'can_undo': cmd.can_undo(),
                'error_message': cmd.error_message
            }
            for cmd in self.command_history
        ]
    
    def clear_history(self):
        """Clear command history"""
        self.command_history.clear()
        self.current_position = -1


class CommandQueue:
    """Queue for managing pending commands"""
    
    def __init__(self):
        self.pending_commands: List[Command] = []
        self.executing_commands: List[Command] = []
        self.completed_commands: List[Command] = []
    
    def add_command(self, command: Command):
        """Add command to queue"""
        command.status = CommandStatus.PENDING
        self.pending_commands.append(command)
    
    def execute_next(self) -> Optional[Command]:
        """Execute next pending command"""
        if not self.pending_commands:
            return None
        
        command = self.pending_commands.pop(0)
        command.status = CommandStatus.EXECUTING
        self.executing_commands.append(command)
        
        success = command.execute()
        
        # Move to completed
        self.executing_commands.remove(command)
        self.completed_commands.append(command)
        
        return command
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status"""
        return {
            'pending': len(self.pending_commands),
            'executing': len(self.executing_commands),
            'completed': len(self.completed_commands)
        }


# Global command invoker instance
command_invoker = CommandInvoker()
command_queue = CommandQueue()