#story_start
The demo console blinks awake inside the test cabin.
A prompt waits for your decision.

* [Inspect the core status] -> core_status
* [Step outside the hatch] -> outside

=== core_status ===
#choice_selected:core
You tap the display; numbers settle at safe levels.
* [Record the reading] -> finish
* [Step back outside] -> outside

=== outside ===
#choice_selected:outside
#smoke
Cool air greets you and a thin ribbon of smoke trails from the vents.
* [Fan the smoke away] -> finish
* [Follow the plume] -> finish

=== finish ===
#story_complete
You radio the all-clear and end the drill.
-> END
