from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship, declarative_base
import time

Base = declarative_base()

# Association table for thread participants (Many-to-Many relationship)
thread_participants = Table(
    'thread_participants', Base.metadata,
    Column('thread_id', String(64), ForeignKey('threads.id'), primary_key=True),
    Column('user_id', String(64), ForeignKey('users.id'), primary_key=True)
)

# Association table for assistant and tools (Many-to-Many relationship)
assistant_tools = Table(
    'assistant_tools', Base.metadata,
    Column('assistant_id', String(64), ForeignKey('assistants.id')),
    Column('tool_id', String(64), ForeignKey('tools.id'))
)

# User model


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), index=True)

    # Relationships
    threads = relationship('Thread', secondary=thread_participants, back_populates='participants')
    assistants = relationship('Assistant', back_populates='user')

# Thread model


class Thread(Base):
    __tablename__ = "threads"

    id = Column(String(64), primary_key=True, index=True)
    created_at = Column(Integer, nullable=False)
    meta_data = Column(JSON, nullable=False, default={})
    object = Column(String(64), nullable=False)
    tool_resources = Column(JSON, nullable=False, default={})

    # Relationship with participants (users)
    participants = relationship('User', secondary=thread_participants, back_populates='threads')

# Message model



class Message(Base):
    __tablename__ = "messages"

    id = Column(String(64), primary_key=True, index=True)
    assistant_id = Column(String(64), index=True)
    attachments = Column(JSON, default=[])
    completed_at = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(Integer, nullable=False)
    incomplete_at = Column(Integer, nullable=True)
    incomplete_details = Column(JSON, nullable=True)
    meta_data = Column(JSON, nullable=False, default={})
    object = Column(String(64), nullable=False)
    role = Column(String(32), nullable=False)
    run_id = Column(String(64), nullable=True)
    status = Column(String(32), nullable=True)
    thread_id = Column(String(64), nullable=False)
    sender_id = Column(String(64), nullable=False)

# Run model


class Run(Base):
    __tablename__ = "runs"

    id = Column(String(64), primary_key=True)
    assistant_id = Column(String(64), nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(Integer, default=lambda: int(time.time()))
    expires_at = Column(Integer, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    incomplete_details = Column(String(256), nullable=True)
    instructions = Column(String(1024), nullable=True)
    last_error = Column(String(256), nullable=True)
    max_completion_tokens = Column(Integer, nullable=True)
    max_prompt_tokens = Column(Integer, nullable=True)
    meta_data = Column(JSON, nullable=True)
    model = Column(String(64), nullable=True)
    object = Column(String(64), nullable=False)
    parallel_tool_calls = Column(Boolean, default=False)
    required_action = Column(String(256), nullable=True)
    response_format = Column(String(64), nullable=True)
    started_at = Column(DateTime, nullable=True)
    status = Column(String(32), nullable=False)
    thread_id = Column(String(64), nullable=False)
    tool_choice = Column(String(64), nullable=True)
    tools = Column(JSON, nullable=True)
    truncation_strategy = Column(JSON, nullable=True)
    usage = Column(JSON, nullable=True)
    temperature = Column(Integer, nullable=True)
    top_p = Column(Integer, nullable=True)
    tool_resources = Column(JSON, nullable=True)

    # One-to-many relationship with actions
    actions = relationship("Action", back_populates="run")

# Assistant model


class Assistant(Base):
    __tablename__ = "assistants"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey('users.id'), nullable=False)
    object = Column(String(64), nullable=False)
    created_at = Column(Integer, nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(String(256), nullable=True)
    model = Column(String(64), nullable=False)
    instructions = Column(String(1024), nullable=True)
    meta_data = Column(JSON, nullable=True)
    top_p = Column(Integer, nullable=True)
    temperature = Column(Integer, nullable=True)
    response_format = Column(String(64), nullable=True)

    # Eager load tools using joinedload to avoid lazy loading issues
    tools = relationship("Tool", secondary=assistant_tools, back_populates="assistants", lazy="joined")
    user = relationship("User", back_populates="assistants")

# Tool model


class Tool(Base):
    __tablename__ = "tools"

    id = Column(String(64), primary_key=True, index=True)
    type = Column(String(64), nullable=False)
    function = Column(JSON, nullable=True)  # JSON field for storing function data, including the name

    # Many-to-many relationship with assistants
    assistants = relationship("Assistant", secondary=assistant_tools, back_populates="tools")

    # One-to-many relationship with actions
    actions = relationship("Action", back_populates="tool")

# Action model


class Action(Base):
    __tablename__ = "actions"

    id = Column(String(64), primary_key=True, index=True)  # ID column
    tool_id = Column(String(64), ForeignKey('tools.id'), nullable=False)  # Reference to the tool
    run_id = Column(String(64), ForeignKey('runs.id'), nullable=False)  # Reference to the run that triggered this action
    triggered_at = Column(DateTime, default=lambda: time.strftime('%Y-%m-%d %H:%M:%S'))  # When the tool was triggered
    expires_at = Column(DateTime, nullable=True)  # When the action expires, if applicable
    is_processed = Column(Boolean, default=False)  # Flag to check if the action has been processed
    processed_at = Column(DateTime, nullable=True)  # Timestamp when the action was processed
    status = Column(String(32), nullable=False, default="pending")  # Status: pending, processing, completed, failed
    function_args = Column(JSON, nullable=True)  # Store the function arguments passed to the tool's function
    result = Column(JSON, nullable=True)  # Store the result of the tool call

    # Relationship with the tool
    tool = relationship("Tool", back_populates="actions")

    # Relationship with the run
    run = relationship("Run", back_populates="actions")
