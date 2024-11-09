# Create & Maintain Salt Formulae

A [Copier][copier-repo] template that initializes a project structure for developing [Salt][salt-repo] formulae.

It's an opinionated variant of the [official template-formula][template-formula] and began its life as a [Cookiecutter/Cruft template][cruft-template].

## Migration from previous template
### `salt-template-formula`
Template version `0.0.1` is identical to the last Cruft template.
Expect this template to diverge significantly from the `template-formula` in future releases.

You can use the following command inside the project root to migrate to this template (requires `jq`):

```bash
jq '.context.cookiecutter |
    with_entries(select(.key | test("^[^_]"))) |
    with_entries(.key |=
        if . == "name" then "service_name"
        elif . == "abbr" then "service_abbr"
        elif . == "git_username" then "author"
        else . end) |
    with_entries(if .key == "needs_repo" then .value = .value == "y" else . end)
' .cruft.json > tmp_copier_answers && \
copier copy --trust --vcs-ref=0.0.1 https://github.com/lkubb/salt-formula-copier --data-file=tmp_copier_answers --skip \* . && \
git add --intent-to-add .copier-answers.yml && \
git clean -ffd && \
rm -f .cruft.json && \
git commit --no-verify -am "Migrate to Copier template"; rm -f tmp_copier_answers
```

You should then immediately update (at least to version `0.0.2`, which excludes `.copier-answers.yml` from pre-commit YAML linting, but leaves everything else as before)

```bash
copier update --trust --skip-answered  # --vcs-ref=0.0.2
```

### `salt-template-formula-compose`
For projects generated from the [compose template-formula][cruft-compose], you can follow similar steps as documented for `salt-template-formula`.
In general, substitute `0.0.1` with `0.0.3` and `0.0.2` with `0.0.4`.
Use the following command:

```bash
jq '.context.cookiecutter |
    with_entries(select(.key | test("^[^_]"))) |
    with_entries(.key |=
        if . == "name" then "service_name"
        elif . == "abbr" then "service_abbr"
        elif . == "git_username" then "author"
        else . end)
' .cruft.json > tmp_copier_answers && \
copier copy --trust --vcs-ref=0.0.3 https://github.com/lkubb/salt-formula-copier --data flavor=compose --data-file=tmp_copier_answers --skip \* . && \
git add --intent-to-add .copier-answers.yml && \
git clean -ffd && \
rm -f .cruft.json && \
git commit --no-verify -am "Migrate to Copier template"; rm -f tmp_copier_answers
```

## Acknowledgement
This project is heavily based on the excellent work done in [saltstackformulas/template-formula][template-formula].

## References
* [Copier docs][copier-docs]

[copier-repo]: https://github.com/copier-org/copier
[salt-repo]: https://github.com/saltstack/salt
[copier-docs]: https://copier.readthedocs.io/en/stable/
[template-formula]: https://github.com/saltstack-formulas/template-formula
[cruft-template]: https://github.com/lkubb/salt-template-formula
[cruft-compose]: https://github.com/lkubb/salt-template-formula-compose
