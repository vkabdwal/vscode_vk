"""
Parallel portfolio evaluation using multiprocessing.
Each worker process gets its own OpenDSS instance (global state is per-process).
"""
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from ..simulation.portfolios import apply_portfolio_to_profiles, summarize_results, score_portfolio
from ..simulation.portfolios import line_capacity_multiplier, transformer_capacity_multiplier

# Use available CPUs (min 2) for parallel portfolio evaluation
MAX_WORKERS = max(2, os.cpu_count() or 2)


def _eval_portfolio_batch(args):
    """Worker function for multiprocessing.
    
    Each worker compiles the feeder in its own process, then evaluates
    a batch of portfolios sequentially using the compile-once pattern.
    """
    portfolios_batch, profiles_dict, base_stress, use_epri, is_capex = args

    import pandas as pd
    from feederiq.backend.simulation.portfolios import (
        apply_portfolio_to_profiles, summarize_results, score_portfolio,
        line_capacity_multiplier, transformer_capacity_multiplier,
    )

    profiles = pd.DataFrame(profiles_dict)

    if use_epri:
        from feederiq.backend.simulation.engine_epri import prepare_epri_simulation, run_epri_24hr_fast
        ctx = prepare_epri_simulation()
        run_fn = run_epri_24hr_fast
    else:
        from feederiq.backend.simulation.engine import prepare_simulation, run_24hr_fast
        ctx = prepare_simulation()
        run_fn = run_24hr_fast

    results = []
    for portfolio in portfolios_batch:
        modified = apply_portfolio_to_profiles(profiles, portfolio)
        if is_capex:
            cap_line = line_capacity_multiplier(portfolio.get("TransformerUpgrade", 0))
            cap_xf = transformer_capacity_multiplier(portfolio.get("TransformerUpgrade", 0))
        else:
            cap_line = line_capacity_multiplier(0)
            cap_xf = transformer_capacity_multiplier(0)

        sim_results = run_fn(ctx, modified, portfolio, cap_mult_line=cap_line, cap_mult_xf=cap_xf)
        alt_summary = summarize_results(sim_results)
        improvement = max(0.0, (base_stress - alt_summary["grid_stress_score"]) / base_stress * 100.0)
        score_row = score_portfolio(portfolio, improvement)
        score_row["alt_summary"] = alt_summary
        results.append(score_row)

    return results


def evaluate_portfolios_parallel(portfolios, profiles, base_stress, use_epri=False, is_capex=False):
    """Evaluate portfolios using multiprocessing if beneficial, else sequential.
    
    Falls back to sequential (compile-once) if portfolio count is small or
    multiprocessing fails.
    """
    n = len(portfolios)
    if n == 0:
        return []

    # For small batches, sequential with compile-once is faster (no spawn overhead)
    if n <= 6 or MAX_WORKERS < 2:
        return _eval_sequential(portfolios, profiles, base_stress, use_epri, is_capex)

    # Split portfolios into batches for workers
    n_workers = min(MAX_WORKERS, n)
    batch_size = (n + n_workers - 1) // n_workers
    batches = [portfolios[i:i + batch_size] for i in range(0, n, batch_size)]

    profiles_dict = profiles.to_dict(orient='list')
    args_list = [(batch, profiles_dict, base_stress, use_epri, is_capex) for batch in batches]

    try:
        scored = []
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = [executor.submit(_eval_portfolio_batch, args) for args in args_list]
            for future in as_completed(futures):
                scored.extend(future.result())
        return scored
    except Exception:
        # Fallback to sequential if multiprocessing fails
        return _eval_sequential(portfolios, profiles, base_stress, use_epri, is_capex)


def _eval_sequential(portfolios, profiles, base_stress, use_epri, is_capex):
    """Sequential evaluation with compile-once (fallback)."""
    if use_epri:
        from feederiq.backend.simulation.engine_epri import prepare_epri_simulation, run_epri_24hr_fast
        ctx = prepare_epri_simulation()
        run_fn = run_epri_24hr_fast
    else:
        from feederiq.backend.simulation.engine import prepare_simulation, run_24hr_fast
        ctx = prepare_simulation()
        run_fn = run_24hr_fast

    scored = []
    for portfolio in portfolios:
        modified = apply_portfolio_to_profiles(profiles, portfolio)
        if is_capex:
            cap_line = line_capacity_multiplier(portfolio.get("TransformerUpgrade", 0))
            cap_xf = transformer_capacity_multiplier(portfolio.get("TransformerUpgrade", 0))
        else:
            cap_line = line_capacity_multiplier(0)
            cap_xf = transformer_capacity_multiplier(0)

        sim_results = run_fn(ctx, modified, portfolio, cap_mult_line=cap_line, cap_mult_xf=cap_xf)
        alt_summary = summarize_results(sim_results)
        improvement = max(0.0, (base_stress - alt_summary["grid_stress_score"]) / base_stress * 100.0)
        score_row = score_portfolio(portfolio, improvement)
        score_row["alt_summary"] = alt_summary
        scored.append(score_row)

    return scored
