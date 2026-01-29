from __future__ import annotations

from agent.config import load_project
from agent.io import ep_dir
from agent.registry import StepContext, register


@register("shotlist")
def run_shotlist(ctx: StepContext) -> None:
    """Generate a deterministic shotlist.csv according to specs/budget.yaml (方案1)."""

    import csv
    import random

    project = load_project(ctx.root)
    ep = ep_dir(project.root, ctx.episode)

    out_path = ep / "shotlist.csv"
    if out_path.exists() and not ctx.force:
        return

    budget = project.budget.get("per_episode", {}) if project.budget else {}
    total_shots = int(budget.get("total_shots_target", 250))
    video_target = int(budget.get("video_clips_target", 5))
    clip_dur = int(budget.get("video_clip_duration_sec", 3))

    rng = random.Random(1000 + ctx.episode)

    scenes = [
        ("SC01", "hook", "L1", "青岚宗外门院", "daylight", 0.14),
        ("SC02", "setup", "L1", "管事处", "indoor soft", 0.12),
        ("SC03", "escalation_1", "L3", "藏经阁外", "warm lantern", 0.18),
        ("SC04", "mid_turn", "L4", "后山废井口", "moonlight rim", 0.16),
        ("SC05", "escalation_2", "L4", "废井深处", "low light", 0.24),
        ("SC06", "cliffhanger", "L1", "外门院深夜", "night lantern", 0.16),
    ]

    alloc = [round(total_shots * w) for *_, w in scenes]
    while sum(alloc) != total_shots:
        delta = total_shots - sum(alloc)
        i = max(range(len(alloc)), key=lambda k: scenes[k][5])
        alloc[i] += 1 if delta > 0 else -1

    neg = "blurry|lowres|deformed hands|extra fingers|text|watermark|logo|bad anatomy"

    video_plan = [
        ("SC01", "hook", "C1", "C1压住怒意，玉坠微热，抬眼", "我只求考核资格。", "爆发前的隐忍", "MCU", "slow push-in", "C1_jade_pendant", "refpacks/C1", 223402),
        ("SC01", "hook", "C2", "C2冷笑特写，压迫感拉满", "资格？你连活着都不配。", "嘲讽", "CU", "handheld slight", "", "refpacks/C2", 223403),
        ("SC04", "mid_turn", "C1", "脚下一滑险坠井，玉坠裂开仙箓浮现", "以命换路，以弱破局。", "惊惧/顿悟", "CU", "handheld shake", "C1_jade_pendant|rune_scroll", "refpacks/C1", 223406),
        ("SC06", "cliffhanger", "C1|C2", "C2伸手索要法器，C1第一次拒绝", "东西给我。", "对峙", "MCU", "slow push-in", "lost_artifact", "refpacks/C1;refpacks/C2", 223409),
        ("SC06", "cliffhanger", "C1", "C1抬眼说“不”，符文补全", "不。", "决绝", "CU", "handheld micro", "rune_scroll|lost_artifact", "refpacks/C1", 223410),
    ]

    video_plan = video_plan[: max(0, min(video_target, len(video_plan)))]

    video_by_scene = {}
    for item in video_plan:
        video_by_scene.setdefault(item[0], []).append(item)

    header = (
        "shot_id,episode,scene_id,beat,start_time_sec,duration_sec,location_id,location_name,characters,"
        "action,dialogue,emotion,shot_type,camera,movement,composition,props,wardrobe,lighting,style_keywords,"
        "continuity_notes,storyboard_prompt,video_prompt,negative_prompt,seed,reference_pack,output_type,output_path,priority"
    ).split(",")

    def mk_prompt(loc, light, chars, action, emotion, extra=""):
        base = f"Vertical 9:16, cinematic realistic live-action ancient xianxia, {loc}, {light}, characters {chars}, {action}, emotion {emotion}."
        return (base + (" " + extra if extra else "")).strip()

    def choose_duration(beat):
        if beat == "hook":
            return rng.choice([2, 2, 3, 3, 4])
        if beat == "cliffhanger":
            return rng.choice([2, 3, 3, 4, 4, 5])
        return rng.choice([3, 3, 3, 4, 4, 5])

    rows = []
    start = 0
    sid = 1
    style = "cinematic|realistic|ancient|9:16"
    wardrobe_C1 = "C1:dark-blue hanfu"
    wardrobe_C2 = "C2:black robe silver pattern"

    for (scene_id, beat, loc_id, loc_name, lighting, _w), n in zip(scenes, alloc):
        vids = video_by_scene.get(scene_id, [])
        video_slots = set()
        if vids:
            for j in range(len(vids)):
                video_slots.add(int((j + 1) * n / (len(vids) + 1)))
        vid_iter = iter(vids)

        for i in range(n):
            shot_id = f"S{sid:04d}"; sid += 1
            duration = choose_duration(beat)
            characters = "C1|C2" if scene_id in ("SC01", "SC03", "SC06") else "C1"
            props = ""
            wardrobe = wardrobe_C1 if "C2" not in characters else f"{wardrobe_C1}; {wardrobe_C2}"
            shot_type = rng.choice(["CU", "MCU", "MS", "WS"])
            camera = "eye-level"
            movement = rng.choice(["static", "static", "slow push-in", "handheld slight"])
            composition = rng.choice(["rule-of-thirds", "center", "two-shot", "over-shoulder", "diagonal"])

            action = ""; dialogue = ""; emotion = ""
            output_type = "storyboard"; priority = "mid"; video_prompt = ""
            seed = 100000 + sid
            refpack = "refpacks/C1" if "C2" not in characters else "refpacks/C1;refpacks/C2"

            if scene_id == "SC01":
                action = rng.choice(["众人围观，压力逼近", "木剑落地特写", "C1握拳忍耐", "C2冷笑逼近", "人群窃笑切镜"])
                emotion = rng.choice(["压迫", "羞辱", "隐忍", "愤怒"])
                dialogue = rng.choice(["来，废柴。", "示范一下不配。", "资格？", "……", "我只求考核资格。"])
                props = rng.choice(["wood_sword", "C1_jade_pendant", ""]) 
            elif scene_id == "SC02":
                action = rng.choice(["名册合上", "管事摆手拒绝", "C1递上木牌", "柜台敲响", "门外脚步声"])
                emotion = rng.choice(["受挫", "压抑", "窘迫"])
                dialogue = rng.choice(["名册上没你。", "别浪费宗门资源。", "陆师兄说了。", "……"])
                props = rng.choice(["register_book", "token", ""]) 
            elif scene_id == "SC03":
                action = rng.choice(["灯笼晃动", "执事拦下", "C2假意解围", "绳索递出", "门规牌匾特写"])
                emotion = rng.choice(["紧张", "伪善", "冷淡"])
                dialogue = rng.choice(["止步。", "他只是想看看门规。", "去后山废井。", "……"])
                props = rng.choice(["lantern", "rope", ""]) 
            elif scene_id == "SC04":
                action = rng.choice(["井口阴风", "脚步打滑", "玉坠发热", "裂痕蔓延", "符文光点浮现"])
                emotion = rng.choice(["恐惧", "顿悟", "震惊"])
                dialogue = rng.choice(["……", "以命换路。", "以弱破局。"])
                props = rng.choice(["C1_jade_pendant", "rune_scroll", "rope"]) 
            elif scene_id == "SC05":
                action = rng.choice(["石壁滑落碎屑", "绳结收紧", "黑影逼近", "呼吸急促", "手抓到法器"])
                emotion = rng.choice(["决绝", "紧张", "痛苦"])
                dialogue = rng.choice(["我不会按你们的结局走。", "再来！", "……"])
                props = rng.choice(["rope", "lost_artifact", ""]) 
            elif scene_id == "SC06":
                action = rng.choice(["灯影拉长", "C2伸手索要", "C1护住法器", "符文一闪", "众人惊住"])
                emotion = rng.choice(["对峙", "爆发", "凝固"])
                dialogue = rng.choice(["东西给我。", "不。", "你敢？", "……"])
                props = rng.choice(["lost_artifact", "rune_scroll", ""]) 

            continuity_notes = []
            if "C1" in characters:
                continuity_notes.append("C1半束发髻+深蓝常驻道袍+玉坠一致")
            if "C2" in characters:
                continuity_notes.append("C2黑衣银纹+高发髻+银剑穗一致")
            if "rune_scroll" in props:
                continuity_notes.append("符文为古风发光符号，避免现代字体")

            storyboard_prompt = mk_prompt(loc_name, lighting, characters, action, emotion, extra="no modern text")

            if i in video_slots:
                try:
                    (_sc, _bt, chars_v, action_v, dialogue_v, emotion_v, shot_type_v, movement_v, props_v, refpack_v, seed_v) = next(vid_iter)
                    characters = chars_v
                    action = action_v
                    dialogue = dialogue_v
                    emotion = emotion_v
                    shot_type = shot_type_v
                    movement = movement_v
                    props = props_v
                    refpack = refpack_v
                    seed = seed_v
                    output_type = "video"
                    priority = "high"
                    wardrobe = wardrobe_C1 if "C2" not in characters else f"{wardrobe_C1}; {wardrobe_C2}"
                    storyboard_prompt = mk_prompt(loc_name, lighting, characters, action, emotion, extra="cinematic realism")
                    video_prompt = mk_prompt(loc_name, lighting, characters, action, emotion, extra=f"{clip_dur}s video, slight camera move, cinematic realistic")
                    duration = clip_dur
                except StopIteration:
                    pass

            out_dir = "clips" if output_type == "video" else "storyboard"
            ext = "mp4" if output_type == "video" else "png"
            output_path = f"episodes/ep{ctx.episode:04d}/{out_dir}/{shot_id}.{ext}"

            rows.append({
                "shot_id": shot_id,
                "episode": str(ctx.episode),
                "scene_id": scene_id,
                "beat": beat,
                "start_time_sec": str(start),
                "duration_sec": str(duration),
                "location_id": loc_id,
                "location_name": loc_name,
                "characters": characters,
                "action": action,
                "dialogue": dialogue,
                "emotion": emotion,
                "shot_type": shot_type,
                "camera": camera,
                "movement": movement,
                "composition": composition,
                "props": props,
                "wardrobe": wardrobe,
                "lighting": lighting,
                "style_keywords": style,
                "continuity_notes": "; ".join(continuity_notes),
                "storyboard_prompt": storyboard_prompt,
                "video_prompt": video_prompt,
                "negative_prompt": neg,
                "seed": str(seed),
                "reference_pack": refpack,
                "output_type": output_type,
                "output_path": output_path,
                "priority": priority,
            })
            start += duration

    # Adjust total to 900 seconds (15min)
    target = 900
    if start != target and rows:
        delta = target - start
        last = rows[-1]
        last_dur = max(1, int(float(last["duration_sec"]) + delta))
        last["duration_sec"] = str(last_dur)

    ep.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
