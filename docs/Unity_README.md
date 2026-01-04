Unity Project README

Unity Editor Version
- Use Unity 6.2 (editor). This project was developed targeting Unity 6.2. Use the Unity Hub or your preferred editor installation manager to install or select Unity 6.2 before opening the project.

How to open the project
1. Install Unity 6.2 via Unity Hub or your preferred installer.
2. Open Unity Hub and click "Add" then select this project's root folder (the repository root containing the `Assets/` and `ProjectSettings/` folders).
3. After adding, launch the project with the Unity 6.2 editor from the Hub.
4. If prompted to upgrade or reimport assets, follow the editor prompts. Prefer creating a backup branch before performing major upgrades.

M0 Scene Path
- The M0 scaffold scene is located at: `Assets/Scenes/M0_Scaffold.unity`
- If the file is not present, this README acts as a placeholder: create the scene at the path above and commit it (see LFS guidance below) or provide an external artifact.

Unity Binary Handling & LFS Guidance
- Unity produces large binary files (e.g., library caches, certain imported assets, .unity scenes with embedded data). Decide whether the repository will store Unity binary assets in Git or keep them in an external artifact store.

Recommendations:
- Commit source-controlled Unity files only: `Assets/`, `ProjectSettings/`, `Packages/` and scene files that are part of development. Do NOT commit the `Library/` directory or editor caches.
- Use Git LFS for large binary assets (textures, audio, large models) that must be versioned with the repository.

Example `.gitattributes` snippet (for Git LFS)
```
# Unity LFS rules
Assets/**/*.psd filter=lfs diff=lfs merge=lfs -text
Assets/**/*.png filter=lfs diff=lfs merge=lfs -text
Assets/**/*.jpg filter=lfs diff=lfs merge=lfs -text
Assets/**/*.tga filter=lfs diff=lfs merge=lfs -text
Assets/**/*.fbx filter=lfs diff=lfs merge=lfs -text
Assets/**/*.unity filter=lfs diff=lfs merge=lfs -text
Assets/**/*.mp4 filter=lfs diff=lfs merge=lfs -text
Assets/**/*.wav filter=lfs diff=lfs merge=lfs -text

# Optionally track large package or archive formats
*.zip filter=lfs diff=lfs merge=lfs -text
*.tar.gz filter=lfs diff=lfs merge=lfs -text
```

Notes on committing Unity files
- Ensure `.gitignore` excludes `Library/`, `Temp/`, `obj/`, `Build/`, and other generated folders.
- If you choose to commit scenes and binary assets, set up Git LFS and add the `.gitattributes` file to the repo before adding large assets.

Manual verification steps for reviewers
1. Install Unity 6.2 and open the project via Unity Hub as described above.
2. Open `Assets/Scenes/M0_Scaffold.unity` from the Project window or via `File > Open Scene`.
3. Confirm the scene opens without missing dependencies or errors (note that missing assets may be due to external artifacts not present in the repository).

If you have questions about LFS setup or prefer using an external artifact store, comment on the beads issue `ge-hch.1.2.1` with your preference.
