- Require a non-alphanumeric left boundary before `sk-` in the secret scanner's
  OpenAI and Anthropic key patterns so URLs such as `.../ask-the-league...` no
  longer read as keys; real keys are still rejected.
