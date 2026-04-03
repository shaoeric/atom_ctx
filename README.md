从openviking tag: v0.2.14 切换分支进行重构

感谢openviking的工作，对于企业的agent context engineer的帮助是巨大的。

openviking在0.2.15版本迎来协议上的变更，从apache改为AGPL协议，对于以SaaS服务的企业来说具有一定的限制。

为了避免代码层面的误伤，所以进行了本次小范围重构，并非忽视协议的要求，而是希望企业项目过渡能更平滑。

## Wheel 打包

项目的 Python wheel 打包会在构建阶段同时编译 Python、Rust、Go 和 CMake 相关产物，统一入口如下：

```bash
bash scripts/ci/build-wheel.sh --python python3.12 --clean
```

也可以直接使用 Makefile：

```bash
make build-wheel PYTHON=python3.12
```

可选参数：

- `--version <value>`: 覆盖 wheel 版本，同时透传给 `CTX_VERSION` 与 `setuptools_scm`
- `--out-dir <path>`: 指定 wheel 输出目录
- `--skip-install-build-deps`: 跳过 Python 构建依赖安装
- `--use-build-isolation`: 使用 PEP 517 build isolation

## GitHub Actions 手动触发

仓库已提供手动触发 workflow：`.github/workflows/build-wheel.yml`。

在 GitHub Actions 页面选择 `Build Python Wheel` 后，可配置：

- `python-version`: 构建使用的 Python 版本
- `version-override`: 可选版本覆盖
- `clean`: 是否先清理历史构建产物
- `upload-artifact`: 是否上传生成的 wheel 到 Actions artifact
- `publish`: 是否在构建完成后上传包
- `publish-target`: 上传目标，支持 `testpypi` 与 `pypi`

如果开启发布，需要在仓库 Secrets 中配置：

- `TEST_PYPI_API_TOKEN`: 发布到 TestPyPI 时使用
- `PYPI_API_TOKEN`: 发布到正式 PyPI 时使用

建议先用 `testpypi` 验证流程，确认包内容和安装行为无误后，再切换到 `pypi`。

## 本地上传到 PyPI

构建完成后，可以在本地复用同一套发布脚本：

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<your-pypi-token>
bash scripts/ci/publish-wheel.sh --python python3.12 --repository pypi
```

上传到 TestPyPI：

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<your-testpypi-token>
bash scripts/ci/publish-wheel.sh --python python3.12 --repository testpypi
```

也可以通过 Makefile 调用：

```bash
make publish-wheel PYTHON=python3.12
```

## 本地调试 Workflow

如果本地安装了 `act`，可以用下面的命令模拟 `workflow_dispatch`：

```bash
act workflow_dispatch \
  -W .github/workflows/build-wheel.yml \
  -e .github/act/build-wheel.event.json
```

如果要在 `act` 中测试发布步骤，还需要额外传入 token，例如：

```bash
act workflow_dispatch \
  -W .github/workflows/build-wheel.yml \
  -e .github/act/build-wheel.event.json \
  -s TEST_PYPI_API_TOKEN=<your-testpypi-token>
```

如果需要修改输入参数，直接编辑 `.github/act/build-wheel.event.json` 即可。