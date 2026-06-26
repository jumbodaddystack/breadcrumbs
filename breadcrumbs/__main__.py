"""Enable ``python -m breadcrumbs`` as an alias for the ``crumb`` CLI."""

from breadcrumbs.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
