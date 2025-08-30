import pytest
from unittest.mock import AsyncMock, patch
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.cron.schedule import Scheduler

@pytest.mark.asyncio
async def test_scheduler_initialization():
    """Test scheduler initialization."""
    scheduler = Scheduler()
    
    assert scheduler.scheduler is not None
    assert scheduler.job is None
    assert isinstance(scheduler.scheduler, AsyncIOScheduler)

@pytest.mark.asyncio
@patch('src.cron.schedule.ingest_documents')
async def test_scheduled_ingestion_success(mock_ingest, caplog):
    """Test successful scheduled ingestion."""
    mock_ingest.return_value = 10
    
    scheduler = Scheduler()
    await scheduler.scheduled_ingestion()
    
    assert mock_ingest.called
    assert "Starting scheduled document ingestion" in caplog.text
    assert "Completed ingestion. Processed 10 documents" in caplog.text

@pytest.mark.asyncio
@patch('src.cron.schedule.ingest_documents')
async def test_scheduled_ingestion_error(mock_ingest, caplog):
    """Test scheduled ingestion with error."""
    mock_ingest.side_effect = Exception("Test error")
    
    scheduler = Scheduler()
    await scheduler.scheduled_ingestion()
    
    assert mock_ingest.called
    assert "Error during scheduled ingestion: Test error" in caplog.text

@pytest.mark.asyncio
@patch('src.cron.schedule.ingest_documents')
async def test_scheduler_start_stop(mock_ingest):
    """Test scheduler start and stop."""
    scheduler = Scheduler()
    
    # Start scheduler
    scheduler.start_scheduler()
    assert scheduler.scheduler.running
    assert scheduler.job is not None
    assert scheduler.job.id == "daily_document_ingestion"
    
    # Get scheduler info
    info = scheduler.get_scheduler_info()
    assert info["name"] == "Daily NVIDIA Documentation Ingestion"
    
    # Stop scheduler
    scheduler.stop_scheduler()
    assert not scheduler.scheduler.running

@pytest.mark.asyncio
async def test_scheduler_info_no_job():
    """Test scheduler info when no job is scheduled."""
    scheduler = Scheduler()
    info = scheduler.get_scheduler_info()
    
    assert info["status"] == "No active jobs"

@pytest.mark.asyncio
@patch('src.cron.schedule.Scheduler.scheduled_ingestion')
async def test_global_scheduler_functions(mock_scheduled_ingestion):
    """Test global scheduler functions."""
    from src.cron.schedule import start_scheduled_tasks, stop_scheduled_tasks, scheduler
    
    # Start scheduler
    start_scheduled_tasks()
    assert scheduler.scheduler.running
    
    # Stop scheduler
    stop_scheduled_tasks()
    assert not scheduler.scheduler.running