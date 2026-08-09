from django.core.cache import cache


def tenant_cache_key(school_id, name):
    return f"school:{school_id}:{name}"


def get_cached_or_set(key, callback, timeout=300):
    value = cache.get(key)

    if value is not None:
        return value

    value = callback()
    cache.set(key, value, timeout)

    return value


def clear_school_cache(school_id):
    keys = [
        tenant_cache_key(school_id, "dashboard_stats"),
        tenant_cache_key(school_id, "finance_stats"),
        tenant_cache_key(school_id, "attendance_stats"),
        tenant_cache_key(school_id, "academic_stats"),
    ]

    for key in keys:
        cache.delete(key)