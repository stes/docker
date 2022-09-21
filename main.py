import pathlib
import yaml
import itertools
import typing
import fnmatch


def product_dict(d):
    keys = tuple(d.keys())
    return (
        dict(zip(keys, values)) for values in itertools.product(*list(map(d.get, keys)))
    )


def match(config, template, return_keys=False):
    def _fnmatch(value, pattern):
        if value is None:
            return False
        return fnmatch.fnmatch(value, pattern)

    matches = []
    keys = dict()
    for key, values in template.items():
        match = False
        if isinstance(values, str):
            values = [values]
        else:
            assert isinstance(values, typing.Iterable)
        for pattern in values:
            if _fnmatch(config.get(key, None), pattern):
                match = True
        matches.append(match)
        keys[key] = match
    if return_keys:
        return matches, keys
    return matches


class Config:
    def __init__(self, config):
        self.__data = config
        assert "matrix" in self.__data

    @property
    def template(self):
        return self.__data.get("template", "")

    @property
    def conflicts(self):
        return self.__data.get("conflicts", [])

    @property
    def requirements(self):
        return self.__data.get("requires", [])

    @property
    def extensions(self):
        return self.__data.get("extend", [])

    @property
    def name(self):
        return self.__data.get("name", [])

    def is_conflict(self, config):
        for conflict in self.conflicts:
            if all(match(config, conflict)):
                return True
        return False

    def violates_requirement(self, config):
        for requirement in self.requirements:
            matches = match(config, requirement)
            if matches[0]:
                if not all(matches):
                    return True
        return False

    def extend(self, config):
        for extension in self.extensions:
            matches = match(
                config, {k: extension[k] for k in config.keys() if k in extension}
            )
            if all(matches):
                for k in extension:
                    if k not in config.keys():
                        config[k] = extension[k]
        return config

    def __iter__(self):
        for config in product_dict(self.__data["matrix"]):
            if self.is_conflict(config):
                continue
            if self.violates_requirement(config):
                continue
            config = self.extend(config)
            yield config


class TemplateFile:
    def __init__(self, fname):
        with open(fname, "r") as fh:
            self.__data = yaml.safe_load(fh)
        self.templates = self.__data["_templates"]
        self.alias = self.__data["_alias"]
        self.configs = {
            key: Config(value)
            for key, value in self.__data.items()
            if not key.startswith("_")
        }

    def __iter__(self):
        for value in self.configs.values():
            for config in value:
                output = value.template.format(**config, **self.templates)
                name = value.name.format(**config, **self.templates)
                env = {}
                for _ in range(100):
                    try:
                        output_ = output.format(**self.alias, **env)
                        break
                    except KeyError as e:
                        env[e.args[0]] = f"${{{e.args[0]}}}"
                else:
                    raise KeyError(env)
                output = output_

                yield name, output


if __name__ == "__main__":
    output_dir = pathlib.Path(".")
    output_dir.mkdir(exist_ok=True)
    for name, config in TemplateFile("build_matrix.yaml"):
        print(f"=================== {name} ===================")
        print(config)
        with (output_dir / f"Dockerfile.{name}").open("w") as fh:
            fh.write(config)
