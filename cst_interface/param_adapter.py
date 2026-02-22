def patch_rect_to_cst_params(params):
    """
    Convert AI params -> CST driver params dict
    params = [W, L, feed_w, h, eps_r]
    """
    W, L, feed_w, h, eps_r = params

    return {
        "patch_W": float(W),
        "patch_L": float(L),
        "feed_width": float(feed_w),
        "substrate_h": float(h),
        "eps_r": float(eps_r),

        # Derived (CST-required)
        "substrate_W": float(W + 6*h),
        "substrate_L": float(L + 6*h),
        "eps_eff": 1.0,     # CST doesn’t actually use this numerically
        "feed_type": 0
    }
