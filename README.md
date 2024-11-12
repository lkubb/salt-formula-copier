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

You should then immediately update (at least to version `0.0.8`, which excludes `.copier-answers.yml` from pre-commit YAML linting, but leaves everything else as before, and fixes two template bugs). Choose `general` as the template flavor when updating.

```bash
copier update --trust --skip-answered  # --vcs-ref=0.0.7
```

### `salt-template-formula-compose`
For projects generated from the [compose template-formula][cruft-compose], you can follow similar steps as documented for `salt-template-formula`.
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
echo "flavor_recorded: compose" >> .copier-answers.yml && \
git commit --no-verify -am "Migrate to Copier template"; rm -f tmp_copier_answers
```

Because of a bug in versions <0.0.7, updating from here needs a workaround. Ensure the repo state is completely clean with no untracked files/uncommitted changes before running:

```bash
copier update --trust --skip-answered --vcs-ref=0.0.7 && \
git add .copier-answers.yml  .pre-commit-config && \
git commit -m "Update to template version 0.0.7" && \
git reset --hard HEAD && git clean -ffd
```

### `salt-tool-template-formula`
For projects generated from the [tool template-formula][cruft-tool], you can follow similar steps as documented for `salt-template-formula`.
Use the following command:

```bash
jq '.context.cookiecutter |
    with_entries(select(.key | test("^[^_]"))) |
    with_entries(.key |=
        if . == "name" then "service_name"
        elif . == "abbr" then "service_abbr"
        elif . == "git_username" then "author"
        elif . == "modstate" then "extmods"
        elif . == "usersettings" then "user_settings"
        else . end) |
    with_entries(. |=
        if .key == "needs_repo" then .value = .value == "y"
        elif .key == "extmods" then .value = if .value == "y" then ["execution", "state"] else [] end
        elif .key == "has_service" then .value = .value == "y"
        elif .key == "mac_library" then .value = .value == "y"
        elif .key == "mac_cask" then .value = .value == "y"
        elif .key == "has_xdg" then .value = .value == "y"
        elif .key == "needs_xdg_help" then .value = .value == "y"
        elif .key == "has_conffile_only" then .value = .value == "y"
        elif .key == "has_configsync" then .value = .value == "y"
        elif .key == "has_config_template" then .value = .value == "y"
        elif .key == "has_completions" then .value = .value == "y"
        elif .key == "has_tests" then .value = .value == "y"
        else . end)
' .cruft.json > tmp_copier_answers && \
copier copy --trust --vcs-ref=0.0.5 https://github.com/lkubb/salt-formula-copier --data flavor=app --data-file=tmp_copier_answers --skip \* . && \
git add --intent-to-add .copier-answers.yml && \
git clean -ffd && \
rm -f .cruft.json && \
echo "flavor_recorded: app" >> .copier-answers.yml && \
git commit --no-verify -am "Migrate to Copier template"; rm -f tmp_copier_answers
```

Because of a bug in versions <0.0.7, updating from here needs a workaround. Ensure the repo state is completely clean with no untracked files/uncommitted changes before running:

```bash
copier update --trust --skip-answered --vcs-ref=0.0.7 && \
git add .copier-answers.yml .pre-commit-config docs/index.rst && \
git commit -m "Update to template version 0.0.7" && \
git reset --hard HEAD && git clean -ffd
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
[cruft-tool]: https://github.com/lkubb/salt-tool-template-formula
