# 清单与使用

源 JSON 相对路径按 JSON 所在文件夹解析；也接受绝对本地路径。每项 `id` 唯一，仅字母、数字、横杠、下划线。`kind` 为 image/video/audio/text/file。只包含要交付的文件。

```json
{
  "title": "Example scene · Shot B",
  "version": "v2",
  "changes": ["调整前景、中景和背景的空间关系", "更新镜头运动"],
  "statuses": {"文件": "已生成", "浏览器": "待验证", "Canvas": "尚未同步", "成片": "尚未生成"},
  "limitations": ["白模仅提供空间参考，不能证明真人动作已经改善"],
  "items": [
    {"id": "first-frame", "kind": "image", "title": "开场首帧", "path": "first.png", "note": "当前版"},
    {"id": "white-b", "kind": "video", "title": "B 白模", "path": "white.mp4", "poster": "poster.png", "note": "B段0–15秒／全片15–30秒；空间参考"},
    {"id": "prompt-b", "kind": "text", "title": "B 生成提示词", "path": "prompt.txt"},
    {"id": "source", "kind": "file", "title": "Blender源工程", "path": "scene.blend"}
  ]
}
```

命令（把 `<skill>` 换为本 Skill 的绝对目录）：

```sh
python3 <skill>/scripts/preview.py build /absolute/manifest.json --out /absolute/output/project/v2
python3 <skill>/scripts/preview.py serve /absolute/output/project --port 8768
```

运行服务用可持续会话，记录启动命令和服务根目录；不要用会阻塞整轮的前台等待。若现有服务已覆盖目录，复用它，不重复启动。输出文件有独立文件名，不依赖原目录的 symlink 或相对路径，目录可整体搬迁。大源文件按需求加入，不为每个预览复制无关帧序列。

网页状态由清单提供，不会自动宣称已验证。完成浏览器/Canvas检查后，按实际结果更新本轮草稿的状态或补充核验记录，再交付。生成脚本只保证清单到静态页，不验证内容真实性。
