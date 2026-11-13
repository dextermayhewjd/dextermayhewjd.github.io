# Paddock.register_agent：分段说明精简前记录

2026-11-07 按用户要求精简前保留的说明与示例，仅供回查。[返回当前函数卡](../../02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.register_agent.md)。

### [1] state → lease → endpoint（165–167 行）

```python
state = self._resolve_state(state)
lease = self._leases.get(state.trajectory_id)
endpoint = self._endpoint_for_state(state, lease)
```

1. **确定 state**：当前调用传入的是 SandboxState 对象，_resolve_state 直接返回它；若传入字符串，才按该字符串去 self._states 查询，查不到会报错。
2. **找回 lease**：用 state.trajectory_id 查询 self._leases。这是 init 中保存的环境记录，查不到时得到 None；不是在此新建环境。
3. **取得 endpoint**：优先用 lease.endpoints["blackbox"]，整理 URL 并保留 headers；如果没有这份入口，则用 state.sandbox_url 和空 headers 构造 Endpoint。

**同一次调用的简短例子**：假设 state.trajectory_id="run-a"，self._leases["run-a"] 已有记录，其中 blackbox URL 为 "https://sandbox-a.example/"，headers={}。这三行之后，state 仍是原对象，lease 指向已有记录，endpoint.url 为 "https://sandbox-a.example"。以上是静态示意，尚未发送网络请求。

| 按需回查 | 回来继续的位置 |
| --- | --- |
| [_resolve_state:299](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L299) | 166 行查询 lease |
| [_endpoint_for_state:311](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L311) | 168 行整理 router |

**当前段结束**：已经拿到请求目标 endpoint。接下来才看 [2] 的 router 与 Agent 类型，再到 [3] 客户端调用。

<a id="two-url-directions"></a>

### [2] proxy_public_url：沙箱访问模型代理的默认地址

**self._proxy_public_url 指向 Dressage Proxy，不指向当前 sandbox。** Paddock 在构造时保存这个默认地址，供之后注册 Agent 时使用；public 在这里强调沙箱一侧能够访问，不要求服务公开在互联网上。

| 名称 | 保存什么 | 在本次注册中的作用 |
| --- | --- | --- |
| endpoint.url | 当前 sandbox 内 BlackboxServer 的地址 | 注册请求实际发送到这里 |
| router_url | 调用方为这次注册传入的模型代理地址 | 有值时优先采用；当前 generate 传入 proxy_url() |
| self._proxy_public_url | Paddock 构造时保存的默认模型代理地址 | router_url 未传或为空时使用 |

对应当前函数的这一行：

```python
# 选择并检查模型代理地址，不是选择 sandbox 的地址。
router = _validate_public_proxy_url(router_url or self._proxy_public_url)
```

1. **选择地址**：优先取 router_url；没有值才取 self._proxy_public_url。
2. **检查格式**：辅助函数检查 URL 格式与本地回环等限制；它不发起网络请求，不能凭此确认网络已经连通。
3. **作为配置传过去**：下面调用客户端时传入 router_url=router，客户端将它放到注册正文的 router 字段。HTTP 注册请求仍发送到 endpoint.url。

同一个例子：endpoint.url="https://sandbox-a.example"，选出的 router="http://dressage-proxy.example:8800"。意思是：**给 sandbox-a 发注册请求，告诉它后续模型请求要转发到 dressage-proxy。** 之后 Claude 的请求会先经过沙箱内代理，再到这个上游地址；本轮不展开转发内部。

地址来源见 Paddock.__init__ 中的 self._proxy_public_url 赋值（paddock.py:46）；请求字段见 BlackboxServerClient.register_agent 的 payload["router"]（client.py:77）。
