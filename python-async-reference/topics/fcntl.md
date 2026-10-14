# fcntl — The fcntl and ioctl system calls — Python 3.16.0a1 documentation

- 官方页面：https://docs.python.org/3.16/library/fcntl.html
- 抓取状态：ok
- 纳入理由：Only file-locking functions/constants are in scope; generic ioctl and unrelated file-descriptor operations are excluded from catalog symbols.
- 范围：matched_sections

[总目录](../OFFICIAL-DOCS.md) · [跨主题统计](../TOPIC-USAGE.md)

## 1. 条目与调用位置数

**每格为：直接调用 / 推断方法 / 非调用引用。**

| API / 协议条目 | slime | areal | verl |
| --- | --- | --- | --- |
| [`fcntl.LOCK_EX`](https://docs.python.org/3.16/library/fcntl.html#fcntl.LOCK_EX) | 0 / 0 / 2 | 0 / 0 / 3 | 0 / 0 / 0 |
| [`fcntl.LOCK_NB`](https://docs.python.org/3.16/library/fcntl.html#fcntl.LOCK_NB) | 0 / 0 / 2 | 0 / 0 / 1 | 0 / 0 / 0 |
| [`fcntl.LOCK_SH`](https://docs.python.org/3.16/library/fcntl.html#fcntl.LOCK_SH) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`fcntl.LOCK_UN`](https://docs.python.org/3.16/library/fcntl.html#fcntl.LOCK_UN) | 0 / 0 / 1 | 0 / 0 / 2 | 0 / 0 / 0 |
| [`fcntl.flock`](https://docs.python.org/3.16/library/fcntl.html#fcntl.flock) | 3 / 0 / 0 | 5 / 0 / 0 | 0 / 0 / 0 |
| [`fcntl.lockf`](https://docs.python.org/3.16/library/fcntl.html#fcntl.lockf) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

## 2. 本地源码位置

| 仓库 / 范围 | API | 记录种类 | 源码位置 | 原代码 |
| --- | --- | --- | --- | --- |
| slime / core | `fcntl.flock` | api_call | [slime/data/queue_data_source.py:73](../repositories/slime/source_snapshot/slime/data/queue_data_source.py.txt) · [固定版本](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L73) |                     fcntl.flock(self._checkpoint_lock.fileno(), fcntl.LOCK_EX &#124; fcntl.LOCK_NB) |
| slime / core | `fcntl.LOCK_EX` | api_reference | [slime/data/queue_data_source.py:73](../repositories/slime/source_snapshot/slime/data/queue_data_source.py.txt) · [固定版本](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L73) |                     fcntl.flock(self._checkpoint_lock.fileno(), fcntl.LOCK_EX &#124; fcntl.LOCK_NB) |
| slime / core | `fcntl.LOCK_NB` | api_reference | [slime/data/queue_data_source.py:73](../repositories/slime/source_snapshot/slime/data/queue_data_source.py.txt) · [固定版本](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L73) |                     fcntl.flock(self._checkpoint_lock.fileno(), fcntl.LOCK_EX &#124; fcntl.LOCK_NB) |
| slime / tests | `fcntl.flock` | api_call | [tests/ci/gpu_lock_exec.py:127](../repositories/slime/source_snapshot/tests/ci/gpu_lock_exec.py.txt) · [固定版本](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/ci/gpu_lock_exec.py#L127) |                 fcntl.flock(fd_lock.fd, fcntl.LOCK_UN) |
| slime / tests | `fcntl.LOCK_UN` | api_reference | [tests/ci/gpu_lock_exec.py:127](../repositories/slime/source_snapshot/tests/ci/gpu_lock_exec.py.txt) · [固定版本](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/ci/gpu_lock_exec.py#L127) |                 fcntl.flock(fd_lock.fd, fcntl.LOCK_UN) |
| slime / tests | `fcntl.flock` | api_call | [tests/ci/gpu_lock_exec.py:213](../repositories/slime/source_snapshot/tests/ci/gpu_lock_exec.py.txt) · [固定版本](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/ci/gpu_lock_exec.py#L213) |         fcntl.flock(self.fd, fcntl.LOCK_EX &#124; fcntl.LOCK_NB) |
| slime / tests | `fcntl.LOCK_EX` | api_reference | [tests/ci/gpu_lock_exec.py:213](../repositories/slime/source_snapshot/tests/ci/gpu_lock_exec.py.txt) · [固定版本](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/ci/gpu_lock_exec.py#L213) |         fcntl.flock(self.fd, fcntl.LOCK_EX &#124; fcntl.LOCK_NB) |
| slime / tests | `fcntl.LOCK_NB` | api_reference | [tests/ci/gpu_lock_exec.py:213](../repositories/slime/source_snapshot/tests/ci/gpu_lock_exec.py.txt) · [固定版本](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/ci/gpu_lock_exec.py#L213) |         fcntl.flock(self.fd, fcntl.LOCK_EX &#124; fcntl.LOCK_NB) |
| areal / core | `fcntl.flock` | api_call | [areal/infra/rpc/guard/app.py:209](../repositories/areal/source_snapshot/areal/infra/rpc/guard/app.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/infra/rpc/guard/app.py#L209) |                     fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX &#124; fcntl.LOCK_NB) |
| areal / core | `fcntl.LOCK_EX` | api_reference | [areal/infra/rpc/guard/app.py:209](../repositories/areal/source_snapshot/areal/infra/rpc/guard/app.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/infra/rpc/guard/app.py#L209) |                     fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX &#124; fcntl.LOCK_NB) |
| areal / core | `fcntl.LOCK_NB` | api_reference | [areal/infra/rpc/guard/app.py:209](../repositories/areal/source_snapshot/areal/infra/rpc/guard/app.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/infra/rpc/guard/app.py#L209) |                     fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX &#124; fcntl.LOCK_NB) |
| areal / core | `fcntl.flock` | api_call | [areal/infra/utils/inference_targets.py:66](../repositories/areal/source_snapshot/areal/infra/utils/inference_targets.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/infra/utils/inference_targets.py#L66) |             fcntl.flock(lock_file, fcntl.LOCK_EX) |
| areal / core | `fcntl.LOCK_EX` | api_reference | [areal/infra/utils/inference_targets.py:66](../repositories/areal/source_snapshot/areal/infra/utils/inference_targets.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/infra/utils/inference_targets.py#L66) |             fcntl.flock(lock_file, fcntl.LOCK_EX) |
| areal / core | `fcntl.flock` | api_call | [areal/infra/utils/inference_targets.py:79](../repositories/areal/source_snapshot/areal/infra/utils/inference_targets.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/infra/utils/inference_targets.py#L79) |                 fcntl.flock(lock_file, fcntl.LOCK_UN) |
| areal / core | `fcntl.LOCK_UN` | api_reference | [areal/infra/utils/inference_targets.py:79](../repositories/areal/source_snapshot/areal/infra/utils/inference_targets.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/infra/utils/inference_targets.py#L79) |                 fcntl.flock(lock_file, fcntl.LOCK_UN) |
| areal / core | `fcntl.flock` | api_call | [areal/v2/cli/utils.py:50](../repositories/areal/source_snapshot/areal/v2/cli/utils.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/v2/cli/utils.py#L50) |         fcntl.flock(fp.fileno(), fcntl.LOCK_EX) |
| areal / core | `fcntl.LOCK_EX` | api_reference | [areal/v2/cli/utils.py:50](../repositories/areal/source_snapshot/areal/v2/cli/utils.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/v2/cli/utils.py#L50) |         fcntl.flock(fp.fileno(), fcntl.LOCK_EX) |
| areal / core | `fcntl.flock` | api_call | [areal/v2/cli/utils.py:54](../repositories/areal/source_snapshot/areal/v2/cli/utils.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/v2/cli/utils.py#L54) |             fcntl.flock(fp.fileno(), fcntl.LOCK_UN) |
| areal / core | `fcntl.LOCK_UN` | api_reference | [areal/v2/cli/utils.py:54](../repositories/areal/source_snapshot/areal/v2/cli/utils.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/v2/cli/utils.py#L54) |             fcntl.flock(fp.fileno(), fcntl.LOCK_UN) |
