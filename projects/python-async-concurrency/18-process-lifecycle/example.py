"""Teaching cut: STOP/COMPLETE protocol, then process and Pool cleanup."""

import multiprocessing
import time


def query_single_turn(client, messages, sampling_params):
    return messages + [{"role": "assistant", "content": "4"}], "stop"


def get_rule_based_math_reward(item):
    return int(item["messages"][-1]["content"] == item["label"])


def worker_process(task_queue, done_queue, rollout_func, reward_func, client, sampling_params):
    for item in iter(task_queue.get, "STOP"):
        messages, finish_reason = rollout_func(client, item["prompt"], sampling_params)
        item["messages"] = messages
        output_item = {
            "messages": messages,
            "reward": reward_func(item),
            "instance_id": item["instance_id"],
            "extra_info": {"finish_reason": finish_reason},
        }
        done_queue.put(output_item)
    done_queue.put("COMPLETE")


def read_data_into_queue(task_queue):
    for instance_id in (10, 11):
        task_queue.put({"instance_id": instance_id, "prompt": [], "label": "4"})
    task_queue.put("STOP")


def conversion_worker(value):
    return value * value


def main():
    ctx = multiprocessing.get_context("spawn")
    task_queue, done_queue = ctx.Queue(maxsize=4), ctx.Queue(maxsize=4)
    processes = []
    try:
        process = ctx.Process(
            target=worker_process,
            args=(task_queue, done_queue, query_single_turn, get_rule_based_math_reward, None, {}),
        )
        process.start()
        processes.append(process)
        print("owned worker", process.pid in {child.pid for child in multiprocessing.active_children()})

        producer = ctx.Process(target=read_data_into_queue, args=(task_queue,))
        producer.start()
        processes.append(producer)
        results = []
        while True:
            item = done_queue.get(timeout=10)
            if item == "COMPLETE":
                break
            results.append((item["instance_id"], item["reward"]))
        print("results", sorted(results))
        for process in processes:
            process.join(timeout=5)
            if process.is_alive() or process.exitcode != 0:
                raise RuntimeError("worker did not exit successfully")
        print("joined", all(not process.is_alive() for process in processes))
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join()
            process.close()
        for queue in (task_queue, done_queue):
            queue.close()
            queue.join_thread()

    process = ctx.Process(target=time.sleep, args=(60,))
    process.start()
    try:
        process.join(timeout=0.01)
        print("join timed out", process.is_alive())
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
        if process.is_alive():
            process.kill()
            process.join()
        print("process reaped", not process.is_alive())
        process.close()

    pool = ctx.Pool(2)
    try:
        print("pool", pool.starmap(conversion_worker, [(2,), (3,)]))
        pool.close()
    except BaseException:
        pool.terminate()
        raise
    finally:
        pool.join()


if __name__ == "__main__":
    main()
