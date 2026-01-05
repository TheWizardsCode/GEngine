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

## Smoke Runbook (M0 Scaffold)

This runbook defines the minimum “Smoke” validation for the M0 scaffold. Use it to:
- verify a local editor run behaves as expected
- produce a basic Desktop and WebGL build
- confirm the build loads and runs without fatal runtime errors

### Preconditions

- Unity **6.2** installed.
- Project opens without requiring a forced upgrade (if upgrades are required, do them on a branch).
- The M0 scene exists at: `Assets/Scenes/M0_Scaffold.unity`.

### Run in Editor (happy path)

1. Open the project in Unity.
2. Open the M0 scene: `Assets/Scenes/M0_Scaffold.unity`.
3. Press **Play**.

#### Expected results (definition of “Smoke”)

At minimum, the scene should behave like a tiny VN-style reader scaffold:
- render *something user-visible* immediately on play (typically a text panel or placeholder UI)
- explain in UI copy what would normally be present once real story content exists (e.g., “Story text will appear here”)
- accept at least one input method to advance the state:
  - mouse click / touch tap
  - keyboard (e.g., Space/Enter)
- advance to a visibly different state on input (e.g., new page text, page counter change, or a visible "advanced" indicator)
- run for at least ~30 seconds without throwing fatal errors or spamming exceptions

> NOTE: The exact UI and interactions are refined by `ge-hch.1.2.2` (Implement: Smoke). This runbook is the testable contract. Update it if the implementation chooses a different interaction model.

### Desktop build validation

1. In Unity: **File > Build Settings…**
2. Select your desktop platform (Windows/Mac/Linux) and choose **Switch Platform** if needed.
3. Confirm the **Scenes In Build** list includes `Assets/Scenes/M0_Scaffold.unity`.
4. Click **Build And Run**.

#### Pass criteria

- App launches and loads the M0 scene.
- The same “Expected results” above are observed.
- No fatal errors (crash, hard hang, empty window forever).

### WebGL build validation

1. In Unity: **File > Build Settings…**
2. Select **WebGL** and choose **Switch Platform**.
3. Confirm `Assets/Scenes/M0_Scaffold.unity` is in **Scenes In Build**.
4. Click **Build And Run**.

#### Pass criteria

- The browser loads the WebGL build.
- The scene renders.
- Input works (mouse + touch if on a touch device).
- No fatal runtime errors.

### How to report a Smoke failure

When reporting a failure in `bd` issues, include:
- Unity version string (from Unity Hub)
- platform (Editor/Desktop/WebGL)
- what step failed
- error text (Console for editor; browser console for WebGL)

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
