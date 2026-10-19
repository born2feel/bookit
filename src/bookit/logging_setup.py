import logging


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    # aiogram is very chatty on DEBUG — keep only what matters
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
