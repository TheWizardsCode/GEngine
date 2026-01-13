// Stable demo story for GEngine
// Compact branching sample with terminal endings and a smoke cue.
// Alternate runs rotate paths for validator (minimum two-choice branch).

VAR campfire_log = false
VAR pocket_compass = true
VAR courage = 0
VAR caution = 0

-> start

=== start ===
Hello, wanderer. Welcome back to the ridge.
#smoke
The embers breathe a thin ribbon of smoke into the evening air.
Your companion nods at you, waiting for a decision.
+ [Head toward the pines]
    ~ courage += 1
    -> pines
+ [Stay by the fire]
    ~ caution += 1
    -> campfire
+ [Check the compass]
    ~ pocket_compass = false
    The needle jitters, then settles north. The path is set.
    -> pines
+ [Mark the campsite]
    You arrange stones in a ring, marking where you started.
    -> campfire

=== pines ===
The pines hush the wind. Mist gathers between the trunks.
The smoke tag still clings to your clothes, a reminder of camp.
+ [Follow the faint trail]
    -> trail
+ [Cut through the underbrush]
    ~ courage += 1
    -> underbrush

=== trail ===
Footsteps echo in front of you. A lantern swings.
A stranger whispers, "Looking for the signal?"
+ [Answer honestly]
    "Yes. I need the flare to guide my friends."
    The stranger smiles and hands you a flint and dried moss.
    ~ campfire_log = true
    -> return_with_supplies
+ [Pretend you're lost]
    "Just wandering." The stranger shrugs and leaves.
    The trail fades into darkness.
    -> lost_end

=== underbrush ===
Branches claw at your sleeves. You push through until you find a clearing.
A hollow tree smolders here, smoke curling upward.
+ [Tend the ember]
    You coax the ember into a steady glow.
    ~ campfire_log = true
    -> return_with_supplies
+ [Snuff it out]
    You stamp the ember flat. The clearing falls silent.
    ~ caution += 1
    -> return_empty

=== campfire ===
You stay by the fire. Sparks drift like fireflies.
+ [Add another log]
    If only you had one. Perhaps the forest holds more.
    -> pines
+ [Wait and watch]
    The smoke rises in a slow spiral. Somewhere, an answer will arrive.
    -> waiting_end

=== return_with_supplies ===
You hurry back with ember and tinder.
Your companion grins. "Perfect timing."
+ [Light a signal]
    You build a small pile of branches.
    {campfire_log:
      The ember takes; smoke blooms bright and steady.
    - else:
      It takes effort, but the tinder finally catches.
    }
    A column of smoke marks your position.
    -> rescue_end
+ [Keep the supplies for later]
    You pocket the flint. The night deepens.
    -> quiet_end

=== return_empty ===
You return with empty hands. The campfire is low.
Your companion raises an eyebrow.
+ [Admit you panicked]
    ~ caution += 1
    They nod. "At least we're safe."
    -> quiet_end
+ [Pretend you found nothing]
    "The woods were silent," you say. The smoke thins.
    -> waiting_end

=== rescue_end ===
A horn echoes in the distance. Lanterns appear through the mist.
Your signal worked; friends converge on the camp.
The night ends with relieved laughter.
-> END

=== waiting_end ===
You wait until dawn. No one comes, but the sunrise is kind.
The journey will continue another day.
-> END

=== quiet_end ===
Without a signal, the ridge stays quiet.
You and your companion share the last of the rations and plan anew.
-> END

=== lost_end ===
The trail dissolves into fog. Without the smoke to guide you, you wander until the stars fade.
-> END
