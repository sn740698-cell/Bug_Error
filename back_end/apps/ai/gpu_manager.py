import logging

logger = logging.getLogger(__name__)

class GPUManager:
    """Manages GPU allocations and low-VRAM optimizations (e.g. RTX 2050 4GB)."""

    def __init__(self):
        try:
            import torch
            self.torch_available = True
            self.cuda_available = torch.cuda.is_available()
            self.device = torch.device('cuda' if self.cuda_available else 'cpu')
            if self.cuda_available:
                self.device_name = torch.cuda.get_device_name(0)
                self.total_memory_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
                logger.info(f"GPU Manager initialized: {self.device_name} ({self.total_memory_mb:.1f} MB VRAM)")
            else:
                self.device_name = "CPU"
                self.total_memory_mb = 0
                logger.info("GPU Manager initialized: PyTorch CUDA not active, using CPU mode")
        except ImportError:
            self.torch_available = False
            self.cuda_available = False
            self.device = "cpu"
            self.device_name = "CPU (PyTorch pending)"
            self.total_memory_mb = 0
            logger.info("GPU Manager initialized: PyTorch not installed yet, CPU fallback ready.")

    def get_vram_usage(self) -> dict:
        """Returns allocated and reserved GPU VRAM memory in MB."""
        if not self.cuda_available or not self.torch_available:
            return {"allocated_mb": 0, "reserved_mb": 0, "free_mb": 0, "device": "CPU"}
        
        import torch
        allocated = torch.cuda.memory_allocated(0) / (1024 * 1024)
        reserved = torch.cuda.memory_reserved(0) / (1024 * 1024)
        free = self.total_memory_mb - reserved
        return {
            "device": self.device_name,
            "total_mb": round(self.total_memory_mb, 2),
            "allocated_mb": round(allocated, 2),
            "reserved_mb": round(reserved, 2),
            "free_mb": round(free, 2)
        }

    def clear_vram_cache(self):
        """Clears CUDA memory cache to prevent OOM on low VRAM GPUs."""
        if self.cuda_available and self.torch_available:
            import torch
            torch.cuda.empty_cache()
            logger.info("CUDA memory cache cleared")

gpu_manager = GPUManager()
