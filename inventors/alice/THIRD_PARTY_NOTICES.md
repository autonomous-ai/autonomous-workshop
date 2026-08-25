# Third-party notices

## Peter's text-to-3d CAD validation work

`src/alice/cad_validation.py` adapts portions of
`peterat617/text-to-3d` at commit
`f18aebe4698d92ffccf07d94e2d624b08d30e667`, principally:

- `src/workshop/make/skills/cad/scripts/cadfits.py`
- `src/workshop/make/skills/cad/scripts/check_mesh`

The adaptation covers calibrated fit derivation and strict mesh-topology/body
validation. Alice's fail-closed motion receipt follows the upstream validation
shape but requires an explicit evaluator outcome. No publisher, renderer,
credential path, model runner, or mutable cache/budget/lock implementation from
that repository is included.

The adapted source is licensed as follows:

```text
MIT License

Copyright (c) 2026 Thompson Labs LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
