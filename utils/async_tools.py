#!/usr/bin/env python3
import os
import json
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor

class AsyncTools:
    def __init__(self, max_workers: int = None):
        """
        Initialize async tools
        
        Args:
            max_workers: Maximum number of workers for thread pool
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
    async def run_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Run a function asynchronously
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Any: Function result
        """
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return await self.loop.run_in_executor(
                    self.executor,
                    func,
                    *args
                )
                
        except Exception as e:
            logging.error(f"Error during async execution: {str(e)}")
            raise
            
    async def gather_results(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Gather results from multiple async tasks
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            List[Dict[str, Any]]: Tasks results
        """
        results = []
        
        async def run_task(task: Dict[str, Any]) -> Dict[str, Any]:
            """Execute a task and return its result"""
            try:
                result = await self.run_async(task["func"], *task.get("args", []))
                return {
                    "success": True,
                    "result": result,
                    "task": task.get("name", "unknown")
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "task": task.get("name", "unknown")
                }
                
        # Create coroutines
        coroutines = [run_task(task) for task in tasks]
        
        # Execute coroutines in parallel
        results = await asyncio.gather(*coroutines)
        
        return results
        
    def run_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run a list of tasks asynchronously
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            List[Dict[str, Any]]: Tasks results
        """
        return self.loop.run_until_complete(self.gather_results(tasks))
        
    def cleanup(self):
        """Clean up resources"""
        try:
            self.executor.shutdown(wait=True)
            
            # Close event loop
            if not self.loop.is_closed():
                self.loop.close()
                
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")
            
    def __del__(self):
        """Destructor"""
        self.cleanup()
