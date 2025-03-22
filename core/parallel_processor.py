import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Callable
from datetime import datetime

from utils.logger import logger

class ParallelProcessor:
    """
    Mercury-inspired parallel processing system
    """
    def __init__(self, num_iterations: int = 6):
        self.num_iterations = num_iterations
        self.performance_history = []
        
    async def process(self, task: Dict[str, Any], model: Any, executor: ThreadPoolExecutor) -> Dict[str, Any]:
        """Process task using parallel execution"""
        try:
            # Split task into chunks
            chunks = self._split_task(task)
            
            # Initial coarse generation
            coarse_results = await self._parallel_execute(chunks, self._coarse_generation, executor)
            
            # Refinement phase
            refined_results = await self._parallel_execute(coarse_results, self._refine_output, executor)
            
            # Merge results with consensus
            final_result = self._merge_with_consensus(refined_results)
            
            # Update performance history
            self._update_performance(task, final_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Parallel processing failed: {e}")
            return {'error': str(e)}
            
    def _split_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split task into parallel chunks"""
        chunks = []
        
        if 'text' in task:
            # Split text processing
            chunks.extend(self._split_text_task(task))
        elif 'vision' in task:
            # Split image processing
            chunks.extend(self._split_vision_task(task))
        elif 'audio' in task:
            # Split audio processing
            chunks.extend(self._split_audio_task(task))
            
        return chunks
        
    def _split_text_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text task into chunks"""
        text = task['text']
        chunk_size = len(text) // self.num_iterations
        return [
            {
                'type': 'text',
                'content': text[i:i+chunk_size],
                'position': i // chunk_size
            }
            for i in range(0, len(text), chunk_size)
        ]
        
    def _split_vision_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split vision task into regions"""
        image = task['vision']
        height, width = image.shape[:2]
        regions = []
        
        # Split into grid
        rows = cols = int(self.num_iterations ** 0.5)
        for i in range(rows):
            for j in range(cols):
                region = {
                    'type': 'vision',
                    'content': image[i*height//rows:(i+1)*height//rows,
                                   j*width//cols:(j+1)*width//cols],
                    'position': (i, j)
                }
                regions.append(region)
                
        return regions
        
    def _split_audio_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split audio task into segments"""
        audio = task['audio']
        segment_size = len(audio) // self.num_iterations
        return [
            {
                'type': 'audio',
                'content': audio[i:i+segment_size],
                'position': i // segment_size
            }
            for i in range(0, len(audio), segment_size)
        ]
        
    async def _parallel_execute(self, 
                              items: List[Dict[str, Any]], 
                              func: Callable, 
                              executor: ThreadPoolExecutor) -> List[Dict[str, Any]]:
        """Execute function in parallel"""
        loop = asyncio.get_event_loop()
        tasks = []
        
        for item in items:
            task = loop.run_in_executor(executor, func, item)
            tasks.append(task)
            
        return await asyncio.gather(*tasks)
        
    def _coarse_generation(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Initial coarse generation phase"""
        try:
            result = {'position': chunk['position']}
            
            if chunk['type'] == 'text':
                # Text processing logic
                result['content'] = self._process_text(chunk['content'])
            elif chunk['type'] == 'vision':
                # Vision processing logic
                result['content'] = self._process_vision(chunk['content'])
            elif chunk['type'] == 'audio':
                # Audio processing logic
                result['content'] = self._process_audio(chunk['content'])
                
            return result
            
        except Exception as e:
            logger.error(f"Coarse generation failed: {e}")
            return {'error': str(e)}
            
    def _refine_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Refinement phase for improving initial results"""
        try:
            refined = result.copy()
            
            if 'content' in result:
                if isinstance(result['content'], str):
                    # Refine text
                    refined['content'] = self._refine_text(result['content'])
                elif isinstance(result['content'], bytes):
                    # Refine binary data (image/audio)
                    refined['content'] = self._refine_binary(result['content'])
                    
            return refined
            
        except Exception as e:
            logger.error(f"Refinement failed: {e}")
            return result
            
    def _merge_with_consensus(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge refined results with consensus mechanism"""
        try:
            # Sort results by position
            sorted_results = sorted(results, key=lambda x: x['position'])
            
            # Merge based on type
            if 'type' in sorted_results[0]:
                if sorted_results[0]['type'] == 'text':
                    return self._merge_text_results(sorted_results)
                elif sorted_results[0]['type'] == 'vision':
                    return self._merge_vision_results(sorted_results)
                elif sorted_results[0]['type'] == 'audio':
                    return self._merge_audio_results(sorted_results)
                    
            return {'error': 'Unknown result type'}
            
        except Exception as e:
            logger.error(f"Merge failed: {e}")
            return {'error': str(e)}
            
    def _update_performance(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Update performance history"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'task_type': task.get('type', 'unknown'),
            'success': 'error' not in result,
            'processing_time': result.get('processing_time', 0),
            'tokens_per_second': result.get('tokens_per_second', 0)
        }
        
        self.performance_history.append(metrics)
        
        # Keep history size manageable
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
            
    @property
    def average_performance(self) -> Dict[str, float]:
        """Calculate average performance metrics"""
        if not self.performance_history:
            return {}
            
        metrics = {}
        for key in ['processing_time', 'tokens_per_second']:
            values = [h[key] for h in self.performance_history if key in h]
            if values:
                metrics[key] = sum(values) / len(values)
                
        return metrics