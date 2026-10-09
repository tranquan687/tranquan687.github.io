"""Google Scholar proxy setup shared by the maintenance scripts."""

from scholarly import ProxyGenerator, scholarly


def configure_scholar_proxy() -> None:
    """Configure a proxy before making any Google Scholar requests."""
    proxy_generator = ProxyGenerator()
    try:
        configured = proxy_generator.FreeProxies()
    except Exception as error:
        raise RuntimeError(
            "Could not configure free proxies for Google Scholar. "
            "Set up a supported premium proxy in scholarly if free proxies "
            "are unavailable."
        ) from error

    if configured is False:
        raise RuntimeError(
            "No free proxy could be configured for Google Scholar. "
            "Set up a supported premium proxy in scholarly before retrying."
        )

    scholarly.use_proxy(proxy_generator)
