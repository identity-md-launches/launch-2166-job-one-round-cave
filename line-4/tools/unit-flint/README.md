# Unit Flint

Check arithmetic on measurements with exact rational values and explicit dimensions. The command accepts decimal quantities, parentheses, `+`, `-`, `*`, `/`, and integer powers (`^` or `**`). Addition and subtraction require matching dimensions; conversion requires a matching target unit. It evaluates its own small expression grammar and never executes Python code.

Run from the repository root:

```sh
python3 line-4/tools/unit-flint/unit_flint.py '1.5 km + 350 m' --to m
```

When tried locally, that command printed `1850 m`. The command `python3 line-4/tools/unit-flint/unit_flint.py '2 m + 3 s'` exited with an incompatible-dimensions error pointing to the `+`. Use `--json` for an exact machine-readable value, base value, and dimension vector. A repeating value is printed as an exact fraction. Supported units are `mm cm m km in ft mi`, `mg g kg t`, `ms s min h day`, `B KiB MiB GiB`, plus `mL L N J W`. Compound units use arithmetic, for example `10 km / 2 h --to 'm/s'`.

This first piece does not handle offset temperatures, currencies or exchange rates, uncertainty, or arbitrary named units. The magnitude of each input number and each exponent is bounded so accidental huge calculations fail quickly. It uses only Python's standard library and makes no network requests.
