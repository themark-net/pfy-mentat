### Entry 045: Bonsai 27B — Extreme 1-Bit Quantization for Browser-Based Local Inference

- **URL**: https://x.com/i/status/2077087411079700782
- **Date**: 2026-07-14
- **Poster**: Xenova (@xenovacom)
- **Summary / Key Claims**: Bonsai 27B uses 1-bit quantization to shrink a 54GB model down to just 3.8GB (-93% size) while retaining ~90% of its intelligence. Runs locally in the browser via custom WebGPU kernels (developed with Fable 5 and GPT-5.6 Sol). Represents a major leap in making large models practical for local/browser-based inference.
- **Extracted Repos / Tools**: Model collection on Hugging Face (PrismML Bonsai 27B). Custom WebGPU kernels for browser inference. Strong demonstration of extreme quantization + browser execution.
- **TOOLS.md Link**: New row under Inference & Serving / Extreme Quantization & Browser Inference (high-signal extreme quantization example).
- **Notes**: **High relevance for local/browser inference.** This showcases cutting-edge extreme quantization (1-bit) that makes large models feasible for local and even browser-based deployment. The combination of massive size reduction with strong performance retention is directly useful for practical local LLM setups, especially on resource-constrained devices or in-browser scenarios. High fit for evaluation criteria: Very High Relevance (extreme quantization + browser inference), High Integration Ease (WebGPU/browser-focused), High Reproducibility (HF model + kernels), Low Redundancy. Recommend: (1) Catalog as major extreme quantization / browser inference resource. (2) Strong candidate for testing on local hardware and browser environments. (3) Excellent reference for pushing the boundaries of what can run locally.
- **Status**: Processed and cataloged (added as high-value extreme quantization and browser inference resource; priority for inference category)

## Future Entries Format

When adding new X-sourced tools or papers:

```
### Entry NNN: Short Title

- **URL**: https://x.com/...
- **Date**: YYYY-MM-DD
- **Poster**: @handle (Name)
- **Summary**: 1-2 sentence gist + why relevant to local LLM dev pipelines. Note if paper-based.
- **Extracted Repos/Tools**: List with links or 'Paper only: arxiv link'.
- **TOOLS.md Link**: Row or section reference.
- **Notes**: Any caveats, hype vs substance, feasibility if paper, pipeline fit.
```

*This log ensures the catalog remains grounded in primary social signals while allowing rigorous, staged evaluation separate from viral claims. 'Read a paper' is now a supported recurring workflow for tool discovery.*