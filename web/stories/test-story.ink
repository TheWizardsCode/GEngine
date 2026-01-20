// Character variables. We track just two, using a +/- scale
VAR forceful = 0
VAR evasive = 0


// Inventory Items
VAR teacup = false
VAR gotcomponent = false


// Story states: these can be done using read counts of knots; or functions that collect up more complex logic; or variables
VAR drugged = false
VAR hooper_mentioned = false

VAR losttemper = false
VAR admitblackmail = false

// what kind of clue did we pass to Hooper?
CONST NONE = 0
CONST STRAIGHT = 1
CONST CHESS = 2
CONST CROSSWORD = 3
VAR hooperClueType = NONE

VAR hooperConfessed = false

CONST SHOE = 1
CONST BUCKET = 2
VAR smashingWindowItem = NONE

VAR notraitor = false
VAR revealedhooperasculprit = false
VAR smashedglass = false
VAR muddyshoes = false

VAR framedhooper = false

// What did you do with the component?
VAR putcomponentintent = false
VAR throwncomponentaway = false
VAR piecereturned = false
VAR longgrasshooperframe = false


// DEBUG mode had shortcuts; remove them for CI and always start at `start`.
VAR DEBUG = false
-> start

 /*--------------------------------------------------------------------------------
	Wrap up character movement using functions, in case we want to develop this logic in future
--------------------------------------------------------------------------------*/


 === function lower(ref x)
	~ x = x - 1

 === function raise(ref x)
	~ x = x + 1

/*--------------------------------------------------------------------------------

	Start the story!

--------------------------------------------------------------------------------*/

=== start === 

//  Intro
	- 	They are keeping me waiting. 
		* 	Hut 14[]. The door was locked after I sat down. 
		I don't even have a pen to do any work. There's a copy of the morning's intercept in my pocket, but staring at the jumbled letters will only drive me mad. 
		I am not a machine, whatever they say about me.

	- (opts)
		{|I rattle my fingers on the field table.|}
	 	* 	(think) [Think] 
			They suspect me to be a traitor. They think I stole the component from the calculating machine. They will be searching my bunk and cases. 
		When they don't find it, {plan:then} they'll come back and demand I talk. 
		-> opts
	 	* 	(plan) [Plan]
			{not think:What I am is|I am} a problem—solver. Good with figures, quick with crosswords, excellent at chess. 
			But in this scenario — in this trap — what is the winning play?
			* * 	(cooperate) [Co—operate] 
	 			I must co—operate. My credibility is my main asset. To contradict myself, or another source, would be fatal. 
	 			I must simply hope they do not ask the questions I do not want to answer.
	 			~ lower(forceful)
	 	*	 	[Dissemble] 
			Misinformation, then. Just as the war in Europe is one of plans and interceptions, not planes and bombs. 
			My best hope is a story they prefer to the truth. 
			~ raise(forceful)
	 	*	 	(delay) [Divert] 
			Avoidance and delay. The military machine never fights on a single front. If I move slowly enough, things will resolve themselves some other way, my reputation intact.
			~ raise(evasive)
		* 	[Wait]		
	- 	-> waited

= waited 
	- 	Half an hour goes by before Commander Harris returns. He closes the door behind him quickly, as though afraid a loose word might slip inside.
		"Well, then," he begins, awkwardly. This is an unseemly situation. 
		* 	"Commander."
			He nods. <>
		* 	(tellme) {not start.delay} "Tell me what this is about."
			He shakes his head. 
			"Now, don't let's pretend."
		* 	[Wait]
			I say nothing.
		- 	He has brought two cups of tea in metal mugs: he sets them down on the tabletop between us.
		* 	{tellme} [Deny] "I'm not pretending anything."
			{cooperate:I'm lying already, despite my good intentions.}
			Harris looks disapproving. -> pushes_cup
		* 	(took) [Take one]
			~ teacup = true
			I take a mug and warm my hands. It's <>
		* 	(what2) {not tellme} "What's going on?"
			"You know already."
			-> pushes_cup
		* 	[Wait]
			I wait for him to speak. 
			- - (pushes_cup) He pushes one mug halfway towards me: <>
	- 	a small gesture of friendship. 
		Enough to give me hope?
	 	* 	(lift_up_cup) {not teacup} [Take it] 
				I {took:lift the mug|take the mug,} and blow away the steam. It is too hot to drink. 
				Harris picks his own up and just holds it.
				~ teacup = true
				~ lower(forceful)
	 	* 	{not teacup} [Don't take it] 
				Just a cup of insipid canteen tea. I leave it where it is.
				~ raise(forceful)
			
		* 	{teacup} 	[Drink] 
			I raise the cup to my mouth but it's too hot to drink.

		* 	{teacup} 	[Wait] 		
			I say nothing as -> lift_up_cup

- 	"Quite a difficult situation," {lift_up_cup:he|Harris} begins{forceful <= 0:, sternly}. I've seen him adopt this stiff tone of voice before, but only when talking to the brass. "I'm sure you agree."
		* 	[Agree] 
				"Awkward," I reply
		* 	(disagree) [Disagree] 
				"I don't see why," I reply
			 ~ raise(forceful)
			 ~ raise(evasive)
		* 	[Lie] -> disagree
		* 	[Evade] 
			"I'm sure you've handled worse," I reply casually
			~ raise(evasive)
	- 	{ teacup:
		~ drugged 	= true
		<>, sipping at my tea as though we were old friends
	  	}
		<>.
		 
		-
			* 	[Watch him]
				His face is telling me nothing. I've seen Harris broad and full of laughter. Today he is tight, as much part of the military machine as the device in Hut 5. 

			* 	[Wait]
				I wait to see how he'll respond. 

			* 	{not disagree} [Smile]
				I try a weak smile. It is not returned.
				~ lower(forceful)
		
// Why you're here
	- 	
		"We need that component," he says.
		
	- 	//"There's no alternative, of course," he continues.
		{not missing_reel:
			-> missing_reel -> harris_demands_component
		}
	- 	
	 	* 	[Yes]
			"Of course I do," I answer. 
	 	* (no) [No]
			"No I don't. And I've got work to do..."
		"Work that will be rather difficult for you to do, don't you think?" Harris interrupts. 
		
	 	* 	[Evade]
			-> here_at_bletchley_diversion
	 	* 	[Lie] 
			-> no
	- 	-> missing_reel -> harris_demands_component

=== missing_reel === 
	* 	[The stolen component...]
	* 	[Shrug]
		I shrug. 
		->->
	- 	The reel went missing from the Bombe this afternoon. The four of us were in the Hut, working on the latest German intercept. The results were garbage. It was Russell who found the gap in the plugboard. 
	- 	Any of us could have taken it; and no one else would have known its worth.
	 
	 	* 	{forceful <= 0 }[Panic] They will pin it on me. They need a scapegoat so that the work can continue. I'm a likely target. Weaker than the rest. 
			~ lower(forceful)
	 	* 	[Calculate] My odds, then, are one in four. Not bad; although the stakes themselves are higher than I would like.
			~ raise(evasive)
	 	* 	{evasive >= 0} [Deny] But this is still a mere formality. The work will not stop. A replacement component will be made and we will all be put back to work. We are too valuable to shoot. 
			~ raise(forceful)
	- 	->->


=== here_at_bletchley_diversion
	"Here at Bletchley? Of course."
	~ raise(evasive)
	~ lower(forceful)
	"Here, now," Harris corrects. "We are not talking to everyone. I can imagine you might feel pretty sore about that. I can imagine you feeling picked on. { forceful < 0:You're a sensitive soul.}"

	* (fine) "I'm fine[."]"," I reply. "This is all some misunderstanding and the quicker we have it cleared up the better."
		~ lower(forceful)
		"I couldn't agree more." And then he comes right out with it, with an accusation. 

	* 	{forceful < 0} 	"What do you mean by that?"

	* (sore) { forceful >= 0 } "Damn right[."] I'm sore. Was it one of the others who put you up to this? Was it Hooper? He's always been jealous of me. He's..."
		~ raise(forceful)
		~ hooper_mentioned = true
		The Commander moustache bristles as he purses his lips. "Has he now? Of your achievements, do you think?" 
		It's difficult not to shake the sense that he's { evasive > 1 :mocking|simply humouring} me.
		"Or of your brain? Or something else?"
		* * 	"Of my genius.["] Hooper simply can't stand that I'm cleverer than he is. We work so closely together, cooped up in that Hut all day. It drives him to distraction. To worse."
			"You're suggesting Hooper would sabotage this country's future simply to spite you?" Harris chooses his words like the military man he is, each lining up to create a ring around me.
		 		* * * 	[Yes] 			
	 				"{ forceful > 0:He's petty enough, certainly|I wouldn't put it past him}. He's a creep." { teacup : I set the teacup down.|I wipe a hand across my forehead.}
	 				~ raise(forceful)
	 				~ teacup = false
	 		 * * * 	[No] 			
	 				"No, { forceful >0:of course not|I suppose not}." { teacup :I put the teacup back down on the table|I push the teacup around on its base}. 
	 			 	~ lower(forceful)
	 			 	~ teacup = false
	 		 * * * 	[Evade] 			
	 				"I don't know what I'm suggesting. I don't understand what's going on."
	 				~ raise(evasive)
	 				"But of course you do." Harris narrows his eyes. 
	 				-> done

				- - - 	(suggest_its_a_lie) "All I can say is, ever since I arrived here, he's been looking to ways to bring me down a peg. I wouldn't be surprised if he set this whole affair up just to have me court—martialled."
					"We don't court—martial civilians," Harris replies. "Traitors are simply hung at her Majesty's pleasure."
	 			* * * 	"Quite right[."]"," I answer smartly.
	 			* * * 	(iamnotraitor) "I'm no traitor[."]"," I answer{forceful > 0 :smartly|, voice quivering. "For God's sake!"}
	 			* * * 	[Lie] -> iamnotraitor
	 			- - - He stares back at me. 

		 * * 	"Of my standing.["] My reputation." { forceful > 0:I'm aware of how arrogant I must sound but I plough on all the same.|I don't like to talk of myself like this, but I carry on all the same.} "Hooper simply can't bear knowing that, once all this is over, I'll be the one receiving the knighthood and he..."
				"No—one will be getting a knighthood if the Germans make landfall," Harris answers sharply. He casts a quick eye to the door of the Hut to check the latch is still down, then continues in more of a murmur: "Not you and not Hooper. Now answer me." 
				For the first time since the door closed, I wonder what the threat might be if I do <i>not</i>. 
		 		
		 * * 	[Evade] 			
		 		~ teacup = false
		 		~ raise(forceful)
		 		"How should I know?" I reply, defensively. { teacup :I set the teacup back on the table.}  -> suggest_its_a_lie
		 		
		
	* [Be honest] 	-> sore
	* [Lie] 	-> fine

- 	(done) -> harris_demands_component


=== harris_demands_component ===
	"{here_at_bletchley_diversion:Please|So}. Do you have it?" Harris is {forceful > 3:sweating slightly|wasting no time}: Bletchley is his watch. "Do you know where it is?"
	 	* 	[Yes]
	 		"I do." 
	 		-> admitted_to_something
	 	* (nope) [No] "I have no idea." 
	 			-> silence
	 	* [Lie] 		-> nope
	 	* [Evade] 		
	 		"The component?"
		 ~ raise(evasive)
		 ~ lower(forceful)
		"Don't play stupid," he replies. "{ not missing_reel:The component that went missing this afternoon. }Where is it?"
		
	- 	{ not missing_reel:
		-> missing_reel -> 
	}
	 	* 	[Co-operate] "I know where it is."
			-> admitted_to_something
	 	* (nothing) [Delay] "I know nothing about it." My voice shakes{ forceful > 0:  with anger|; I'm unaccustomed to facing off against men with holstered guns}. 

	 	* 	[Lie] -> nothing
	 	* [Evade] 

		"I don't know what gives you the right to pick on me. { forceful > 0:I demand a lawyer.|I want a lawyer.}"

		"This is time of war," Harris answers.  "And by God, if I have to shoot you to recover the component, I will. Understand?" He points at the mug,-> drinkit

	-	(silence) There's an icy silence. { forceful > 2:I've cracked him a little.|{ evasive > 2:He's tiring of my evasiveness.}} 

	// Drink tea and talk
	- (drinkit) "Now drink your tea and talk."
	 * { teacup  }   	[Drink] 		-> drinkfromcup
	 * { teacup  }   	[Put the cup down] 
	 		I set the cup carefully down on the table once more.
			~ teacup = false
			~ raise(forceful)
			-> whatsinit
	 
	 * { not teacup  }  [Take the cup] 
	 		- - (drinkfromcup) I lift the cup { teacup :to my lips }and sip. He waits for me to swallow before speaking again.
		 	~ drugged  = true
		 	~ teacup    = true
	 * { not teacup  }  [Don't take it] 
	 		I leave the cup where it is. 
			~ raise(forceful)
			- - (whatsinit) "Why?" I ask coldly. "What's in it?"
		
	- 	"Lapsang Souchong," he {drinkfromcup:remarks|replies}, placing his own cup back on the table untouched. "Such a curious flavour. It might almost not be tea at all. You might say it hides a multitude of sins. As do you. Isn't that right?"

		 * (suppose_i_have) [Agree] 
		 	 	// Regrets
			"I suppose so," I reply. "I've done things I shouldn't have done." 
			 ~ lower(forceful)
			 -> harris_presses_for_details

		* (nothing_ashamed_of) { not drugged  }   [Disagree]
				"I've done nothing that I'm ashamed of."
		 		-> harris_asks_for_theory

		 * (cant_talk_right) { drugged  }   [Disagree] 
		 	 	I open my mouth to disagree, but the words I want won't come. It is like Harris has taken a screwdriver to the sides of my jaw.
		 		-> admitted_to_something.ive_done_things

		 * {drugged} [Lie] 	-> cant_talk_right
		 * {not drugged} [Lie] 	-> nothing_ashamed_of
		 * { drugged  }   [Evade] -> cant_talk_right
	
		 * { not drugged  }   [Evade] 
		 		"None of us are blameless, Harris. { forceful > 1:But you're not my priest and I'm not yours|But I've done nothing to deserve this treatment}. Now, please. Let me go. I'll help you find this damn component, of course I will." 
			//   Who do you blame?
			He appears to consider the offer. 
			 -> harris_asks_for_theory



=== harris_presses_for_details
// Open to Blackmail
	"You mean you've left yourself open," Harris answers. "To pressure. Is that what you're saying?"
	  	* [Yes] -> admit_open_to_pressure
	  	* { not drugged  } [No] 
	  			"I'm not saying anything of the sort," I snap back. "What is this, Harris? You're accusing me of treachery but I don't see a shred of evidence for it! Why don't you put your cards on the table?"
	  			~ raise(forceful)
	  			
			
	  	* {drugged} [No] 
	  			I shake my head violently, to say no, that's not it, but whatever is wrong with tongue is wrong with neck too. I look across at the table at Harris' face and realise with a start how sympathetic he is. Such a kind, generous man. How can I hold anything back from him?
	  			~ lower(forceful)
				I take another mouthful of the bitter, strange—tasting tea before answering.
	  			-> admit_open_to_pressure

	  	
	  	* { not drugged  } [Evade] 
	  			"You're the one applying pressure here," I answer { forceful > 1:smartly|somewhat miserably}. "I'm just waiting until you tell me what is really going on."
		 		 ~ raise(evasive)
	  	* { drugged  } [Evade] 				 
	  			"We're all under pressure here."
	  			He looks at me with pity. -> harris_has_seen_it_before

	 	- 	"It's simple enough," Harris says. -> harris_has_seen_it_before

= admit_open_to_pressure
	"That's it," I reply. "There are some things... which a man shouldn't do."
	 ~ admitblackmail  = true
	Harris doesn't stiffen. Doesn't lean away, as though my condition might be infectious. I had thought they trained them in the army to shoot my kind on sight. 
	He offers no sympathy either. He nods, once. His understanding of me is a mere turning cog in his calculations, with no meaning to it.
	-> harris_has_seen_it_before


=== admitted_to_something
	// Admitting Something
	{ not drugged  :
		Harris stares back at me. { evasive == 0:He cannot have expected it to be so easy to break me.}
	- else:
		Harris smiles with satisfaction, as if your willingness to talk was somehow his doing.
	}
	"I see." 
	There's a long pause, like the delay between feeding a line of cypher into the Bombe and waiting for its valves to warm up enough to begin processing. 
	"You want to explain that?"
		 * 	[Explain] 
	 	 	I pause a moment, trying to choose my words. To just come out and say it, after a lifetime of hiding... that is a circle I cannot square.
	 	 	* * 	[Explain] 	-> ive_done_things
	 	 	* * 	{drugged} [Say nothing] 	-> say_nothing
	 	 	* * 	{not drugged} [Lie] 	-> claim_hooper_took_component

		 * { not drugged  }   [Don't explain]
	 	 		"There's nothing to explain," I reply stiffly. -> i_know_where
			
		 * { not drugged  }   [Lie] -> claim_hooper_took_component
		 * { not drugged  }   [Evade]
	 		"Explain what you should be doing, do you mean, rather than bullying me? Certainly." I fold my arms. -> i_know_where

		 * (say_nothing) { drugged  }   [Say nothing]
	 		I fold my arms, intended firmly to say nothing. But somehow, watching Harris' face, I cannot bring myself to do it. I want to confess. I want to tell him everything I can, to explain myself to him, to earn his forgiveness. The sensation is so strong my will is powerless in the face of it. 
			Something is wrong with me, I am sure of it. There is a strange, bitter flavour on my tongue. I taste it as words start to form.
	 		-> ive_done_things

= i_know_where
	"I know where your component is because it's obvious where your component is. That doesn't mean I took it, just because I can figure out a simple problem, any more than it means I'm a German spy because I can crack their codes."
	-> harris_asks_for_theory


= ive_done_things
	 "I've done things," I begin{harris_demands_component.cant_talk_right: helplessly}. "Things I didn't want to do. I tried not to. But in the end, it felt like cutting off my own arm to resist."
	-> harris_presses_for_details




=== harris_asks_for_theory
	"Tell me, then," he asks. "What's your theory? You're a smart fellow — as smart as they come around here, and that's saying something. What's your opinion on the missing component? Accident, perhaps? Or do you blame one of the other men? { hooper_mentioned :Hooper?}"
	  	* [Blame no—one] 
	 		-> an_accident
	 	* [Blame someone] -> claim_hooper_took_component

= an_accident
	"An accident, naturally." I risk a smile. "That damned machine is made from spare parts and string. Even these Huts leak when it rains. It wouldn't take more than one fellow to trip over a cable to shake out a component. Have you tried looking under the thing?"
	"Do you believe we haven't?"
	In a sudden moment I understand that his reply is a threat. 
	"Now," he continues. "Are you sure there isn't anything you want to tell me?"

	 	* [Co-operate]
	 	 	"All right." With a sigh, your defiance collapses. "If you're searched my things then I suppose you've found { evasive > 1: what you need|my letters. Haven't you? In fact, if you haven't, don't tell me}.
		 	 ~ admitblackmail  = true
		 	Harris nods once. 
		 	<> -> harris_has_seen_it_before

	 	* {evasive > 0} [Evade] "Only that you're being unreasonable, and behaving like a swine."
	 	// Loses temper
	 	"You imbecile," Harris replies, with sudden force. He is half out of his chair. "You know the situation as well as I do. Why the fencing? The Hun are poised like rats, ready to run all over this country. They'll destroy everything. You understand that, don't you? You're not so locked up inside your crossword puzzles that you don't see that, are you? This machine we have here — you men — you are the best and only hope this country has. God help her."
	 		~ losttemper  = true
	 		I sit back, startled by the force of his outburst. His carefully sculpted expression has curled to angry disgust. <i>He really does hate me</i>, I think. <i>He'll have my blood for the taste of it.</i>
	 	* * [Placate]
	 		"Now steady on," I reply, gesturing for him to be calm.
	 		
	 	* * [Mock] 
	 		"I can imagine how being surrounded by clever men is pretty threatening for you, Commander," I reply with a sneer. "They don't train you to think in the Armed Forces."
	 		 ~ raise(forceful)
	 		
	 	* * [Dismiss]
	 		"Then I'll be going, on and getting on with my job of saving her, shall I?" I even rise half to my feet, before he slams the tabletop.
	 		
	 	- - "Talk," Harris demands. "Talk now. Tell me where you've hidden it or who you passed it to. Or God help me, I'll take your wretched pansy body to pieces looking for it."
	 	 	-> harris_demands_you_speak





=== harris_has_seen_it_before
	"I've seen it before. A young man like you — clever, removed. The kind that doesn't go to parties. Who takes himself too seriously. Who takes things too far."
	He slides his thumb between two fingers.
	"Now they own you."
	
	 * [Agree] 
	 	"What could I do?" I'm shaking now. The night is cold and the heat—lamp in the Hut has been removed. "{ forceful > 2:I won't|I don't want to} go to prison."
	 	"Smart man," he replies. "You wouldn't last.  
		
	 * [Disagree] 
	 	 "I can still fix this."
	 	Harris shakes his head. "You'll do nothing. This is beyond you now. You may go to prison or may go to firing squad - or we can change your name and move you somewhere where your indiscretions can't hurt you. But right now, none of that matters. What happens to you doesn't matter. All that matters is where that component is. 
		
	 * { not drugged  }   [Lie] 
	 	 "I wanted to tell you," I tell him. "I thought I could find out who they were. Lead you to them."
	 	Harris looks at me with contempt. "You wretch. You'll pay for what you've done to this country today. If a single man loses his life because of your pride and your perversions then God help your soul. 

	*  {drugged} {forceful < 0} [Apologise]
		"Harris, I..."
		~lower(forceful)
		"Stop it," he interrupts. "There's no jury here to sway.  And there's no time. 

- 	(tell_me_now) <> So why don't you tell me, right now. Where is it?"
	-> harris_demands_you_speak




=== harris_demands_you_speak
	His eyes bear down like carbonised drill—bits.
	* [Confess] 
	 	{ forceful > 1 :
		"You want me to tell you what happened? You'll be disgusted."
		-else:
			"All right. I'll tell you what happened." And never mind my shame.
	 	}
		"I can imagine how it starts," he replies.

	 * { not drugged  } [Dissemble] -> claim_hooper_took_component
	 * { drugged  } [Dissemble]
	 	My plan now is to blame Hooper, but I cannot seem to tell the story. Whatever they put in my tea, it rules my tongue. { forceful >1:I fight it as hard as I can but it does no good.|I am desperate to tell him everything. I am weeping with shame.} 
	 	
		 ~ lower(forceful)
-  -> i_met_a_young_man




=== i_met_a_young_man
	//  Explain Story
	* 	[Talk]
		"There was a young man. I met him in the town. A few months ago now. We got to talking. Not about work. And I used my cover story, but he seemed to know it wasn't true. That got me wondering if he might be one of us."
	-	Harris is not letting me off any more. 
		"You seriously entertained that possibility?"
	 	* [Yes]
	 		"Yes, I considered it. <>
	 	* [No] 
		"No. Not for more than a moment, of course. Everyone here is marked out by how little we would be willing to say about it."
		"Only you told this young man more than a little, didn't you?"
		I nod. "<>"
	*	[Lie] 
		"I was quite certain, after a while. After we'd been talking. <>
	- 	He seemed to know all about me. He... he was quite enchanted by my achievements."
		The way Harris is staring I expect him to strike me, but he does not. He replies, "I can see how that must have been attractive to you," with such plain—spokeness that I think I must have misheard.

	 *  [Yes] "It's a lonely life in this place," I reply. "Lonely - and still one never gets a moment to oneself."
	 	"That's how it is in the Service," Harris answers. 
	 	* *	[Argue] "I'm not in the Service."
	 		Harris shakes his head. "Yes, you are."  
	 	* * [Agree] "Perhaps. But I didn't choose this life." 
	 		Harris shakes his head. "No. And there's plenty of others who didn't who are suffering far worse." 
	 	- - Then he waves the thought aside. 

	 * (nope) { not drugged  }  [No] "The boy was a pretty simpleton. Quite inferior. His good opinion meant nothing to be. Harris, do not misunderstand. I was simply after his body."
	 		 ~ raise(evasive)
	 		Harris, to his credit, doesn't flinch; but I can see he will have nightmares of this moment later tonight. I'm tempted to reach out and take his hand to worsen it for him.
	 
	 * { drugged  }   	[No] 
	 		"It wasn't," I reply. "But I doubt you'd understand."
	 		He simply nods. 
	 * { not drugged  }    	[Lie] -> nope

- 	 "Go on with your confession."
- 	(paused) 
	 	 { not nope:
		That gives me pause. I hadn't thought of it as such. But I suppose he's right. I am about to admit what I did.
	 	}
		"There's not much else to say. I took the part from Bombe computing device. You seem to know that already. I had to. He was going to expose me if I didn't."
	 	//  So blackmail?
	 	"This young man was blackmailing you over your affair?"

	 	~ temp harris_thinks_youre_drugged = drugged

	 	 { drugged:
	 	 	~ drugged = false
	 		As Harris speaks I find myself suddenly sharply aware, as if waking from a long sleep. The table, the corrugated walls of the hut, everything seems suddenly more tangible than a moment before. 
	 		Whatever it was they put in my drink is wearing off. 
	 	}
	 	 
	 	 * (yes) [Yes] 
	 	 	"Yes. I suppose he was their agent. I should have realised but I didn't. Then he threatened to tell you. I thought you would have me locked up: I couldn't bear the thought of it. I love working here. I've never been so happy, so successful, anywhere before. I didn't want to lose it."
	 	 	"So what did you do with the component?" Harris talks urgently. He grips his gloves tightly in one hand, perhaps prepared to lift them and strike if it is required. "Have you passed it to this man already? Have you left it somewhere for him to find?" 
	 	 	* * (still_have)	[I have it] 	
	 	 			"I still have it. Not on me, of course. -> reveal_location_of_component

	 	 	* * (dont_have) 	[I don't have it] 	-> i_dont_have_it
	 	 	* * [Lie] 			-> dont_have
	 	 	* * [Tell the truth] 		-> still_have

	 	 * (notright) [No] 
	 	 	"No, Harris. The young man wasn't blackmailing me." I take a deep breath. "It was Hooper."
	 	 	{ not hooper_mentioned:
	 	 		"Hooper!" Harris exclaims, in surprise. {harris_thinks_youre_drugged:He does not doubt me for a moment.}
	 	 	- else:
	 	 		"Now look here," Harris interrupts. "Don't start that again."
	 	 	}
	 	 	 "It's the truth, Harris. If I'm going to jail, so be it, but I won't hang at Traitor's Gate. Hooper was the one who told the boy about our work. Hooper put the boy on to me. { forceful < 2:I should have realised, of course. These things don't happen by chance. I was a fool to think they might.} And then, once he had me compromised, he demanded I steal the part from the machine."
	 	 	 ~ revealedhooperasculprit  = true
	 	 	"Which you did." Harris leans forward. "And then what? You still have it? You've stashed it somewhere?"
	 	 	* * (didnt_have_long) [Yes] 
	 	 		"Yes. I only had a moment. -> reveal_location_of_component

	 	 	* * (passed_on) [No] -> passed_onto_hooper
	 	 	* * [Lie] 		-> passed_on
	 	 	* * [Evade] 		
	 	 		"I can't remember."
	 	 		He draws his gun and lays it lightly on the field table.
	 	 		"I'm sorry to threaten you, friend. But His Majesty needs that brain of yours, and that brain alone. There are plenty of other parts to you that our country could do better without. Now I'll ask you again. Did you hide the component?"
	 	 		* * * [Yes] -> didnt_have_long
	 	 		* * * (nope_didnt_hide) [No] 
	 	 		 		"Very well then." I swallow nervously, to make it look more genuine. -> passed_onto_hooper
	 	 		* * * [Lie] -> nope_didnt_hide 

	 	 		* * * [Evade] -> i_dont_have_it

	 	 * [Tell the truth] 	-> yes
	 	 * [Lie] 		-> notright

= i_dont_have_it
	"I don't have it any more. I passed it through the fence to my contact straight after taking it, before it was discovered to be missing. It would have been idiocy to do differently. It's long gone, I'm afraid."
	"You fool, Manning," Harris curses, getting quickly to his feet. "You utter fool. Do you suppose you will be any better off living under Hitler? It's men like you who will get us all killed. Men too feeble, too weak in their hearts to stand up and take a man's responsibility for the world. You're happier to stay a child all your life and play with your little childish toys."
	 * [Answer back]
	 	"Really, Commander," I reply. "It rather sounds like you want to spank me."
	 	"For God's sake," he declares with thick disgust, then swoops away out of the room.

	 * [Say nothing] 
	 	I say nothing. It's true, isn't it? I can't deny that I know there is a world out there, a complicated world of pain and suffering. And I can't deny that I don't think about it a moment longer than I have to. What use is thinking on a problem that cannot be solved? It is precisely our ability to avoid such endless spirals that makes us human and not machine.
	 	"God have mercy on your soul," Harris says finally, as he gets to his feet and heads for the door. "I fear no—one else will." 

	- -> left_alone

= passed_onto_hooper
	~ hooper_mentioned = true
	"No. I passed it on to Hooper."
	"I see. And what did he do with it?"
	 	* [Evade] 
	 		"I don't know."
		"You can do better than that. Remember, there's a hangman's noose waiting for traitors."
		* * 	[Theorise] 
				"Well, then," I answer, nervously. "What would he do? Either get rid of it straight away — or if that wasn't possible, which it probably wouldn't be, since he'd have to arrange things with his contacts — so most likely, he'd hide it somewhere and wait, until you had the rope around my neck and he could be sure he was safe."
		 		-> claim_hooper_took_component.harris_being_convinced

		* * [Shrug] -> claim_hooper_took_component.its_your_problem

	 	* [Tell the truth] 
	 		"I don't think Hooper could have planned this in advance. So he'd need to get word to whoever he's working with, and that would take time. So I think he would have hidden it somewhere, and be waiting to make sure I soundly take the fall. That way, if anything goes wrong, he can arrange for the part to be conveniently re—found."
	 		-> claim_hooper_took_component.harris_being_convinced

	 	* [Lie]
	 		"I'm sure I saw him this evening, talking to someone by the fence on the woodland side of the compound. He's probably passed it on already. You'll have to ask him."

			 -> claim_hooper_took_component.harrumphs


/*--------------------------------------------------------------------------------
	Trying to frame Hooper
--------------------------------------------------------------------------------*/


=== claim_hooper_took_component
//  Blame Hooper
	"I saw Hooper take it."
	 ~ hooper_mentioned  = true
	 { losttemper  :
		"Did you?" 
		The worst of his rage is passing; he is now moving into a kind of contemptuous despair. I can imagine him wrapping up our interview soon, leaving the hut, locking the door, and dropping the key down the well in the yard. 
		And why wouldn't he? With my name tarnished they will not let me back to work on the Bombe — if there is the slightest smell of treachery about my name I would be lucky not be locked up for the remainder of the war.
	- else:
		 "I see." He is starting to lose his patience. I have seen Harris angry a few times, with lackeys and secretaries. But never with us. With the 'brains' he has always been cautious, treating us like children. 
		 And now I see that, like a father, he wants to smack us when we disobey him.
	}
	"Just get to the truth, man. Every <i>minute</i> matters."
	 * { admitblackmail  }   [Persist with this]
	 		"I know what you're thinking. If I've transgressed once then I must be guilty of everything else... But I'm not. We were close to cracking the 13th's intercept. We were getting correlations in the data. Then Hooper disappeared for a moment, and next minute the machine was down."
	 			
	 	* [Tell the truth] 
	 		"Very well. I see there's no point in covering up. You know everything anyway."
			Harris nods, and waits for me to continue.
			 -> i_met_a_young_man

	 	* { not admitblackmail }   [Persist with this]
	 			"This is the truth."
	 	 
	- 	I have become, somehow, an accustomed liar — the words roll easily off my tongue. Perhaps I am a traitor, I think, now that I dissemble as easily as one.
		"Go on," Harris says, giving me no indication of whether he believes my tale.
	 	 * 	[Assert] "I saw him take it," I continue. "Collins was outside having a cigarette. Peterson was at the table. But I was at the front of the machine. I saw Hooper go around the side. He leant down and pulled something free. I even challenged him. I said, 'What's that? Someone put a nail somewhere they shouldn't have?' He didn't reply."
			Harris watches me for a long moment.
			
	 	 * 	[Imply] "At the moment the machine halted, Peterson was at the bench and Collins was outside having a smoke. I was checking the dip—switches. Hooper was the only one at the back of the Bombe. No—one else could have done it."
			"That's not quite the same as seeing him do it," Harris remarks.
	 	 	 * * 	[Logical]
	 	 	 	"When you have eliminated the impossible..." I begin, but Harris cuts me off.
	 	 	 
	 	 	 * * 	[Persuasive] 
	 	 	 	"You have to believe me." 
	 	 	 	"We don't have to believe anyone," Harris returns. "I will only be happy with the truth, and your story doesn't tie up. We know you've been leaving yourself open to pressure. We've been watching your activities for some time. But we thought you were endangering the reputation of this site; not risking the country herself. Perhaps I put too much trust in your intellectual pride."
			He pauses for a moment, considering something. Then he continues:
			"It might have been Hooper. It might have been you. -> we_wont_guess

	 	 	 * * 	[Confident] 
	 		"Ask the others," I reply, leaning back. "They'll tell you. If they haven't already, that's only because they're protecting Hooper. Hoping he'll come to his senses and stop being an idiot. I hope he does too. And if you lock him up in a freezing hut like you've done me, I'm sure he will."
			"We have," Harris replies simply. 
			It's all I can do not to gape.
			-> hoopers_hut_3

	- 	"We are left with two possibilities. You, or Hooper." The Commander pauses to smooth down his moustache. <>
	- 	(hoopers_hut_3) "Hooper's in Hut 3 with the Captain, having a similar conversation."
	 	 	
	 	 	 * 	"And the other men?[" ] Do we have a hut each? Are there  enough senior officers to go round?"
	 	 		"Collins was outside when it happened, and Peterson can't get round the machine in that chair of his," Harris replies. "That leaves you and Hooper.
	 	 	 * 	"Then you know I'm right.[" ] You knew all along. Why did you threaten me?"
	 	 		"All we know is that we have a traitor, holding the fate of the country in his hands. 
	- (we_wont_guess) <> We're not in the business of guessing here at Bletchley. We are military intelligence. We get answers." Harris points a finger. "And if that component has left these grounds, then every minute is critical."
	 	 * [Co-operate] 
	 		"I'd be happy to help," I answer, leaning forwards. "I'm sure there's something I could do."
	 		"Like what, exactly?"
	 		* * 	"Put me in with Hooper."
	 			 -> putmein
	 		* * 	"Tell Hooper I've confessed.[" ] Better yet. Let him see you marching me off in handcuffs. Then let him go, and see what he does. Ten to one he'll go straight to wherever he's hidden that component and his game will be up."
	 			Harris nods slowly, chewing over the idea. It isn't a bad plan even — except, of course, Hooper has <i>not</i> hidden the component, and won't lead them anywhere. But that's a problem I might be able to solve once I'm out of this place; and once they're too busy dogging Hooper's steps from hut to hut.
	 			"Interesting," the Commander muses. "But I'm not so sure he'd be that stupid. And if he's already passed the part on, the whole thing will only be a waste of time."
	 			* * * 	"Trust me. He hasn't.[" ] If I know that man, and I do, he'll be wanting to keep his options open as long as possible. If the component's gone then he's in it up to his neck. He'll take a week at least to make sure he's escaped suspicion. Then he'll pass it on."
	 				"And if we keep applying pressure to him, you think the component will eventually just turn up?"
	 				* * * * "Yes.[" ] Probably under my bunk."
	 					Harris smiles wryly. "We'll know that for a fake, then. We've looked there already. 
	 				* * * * "Or be thrown into the river." 
	 					"Hmm." Harris chews his moustache thoughtfully. "Well, that would put us in a spot, seeing as how we'd never know for certain. We'd have to be ready to change our whole approach just in case the part had got through to the Germans. 
	 				- - - -	 <> I don't mind telling you, this is a disaster, this whole thing. What I want is to find that little bit of mechanical trickery. I don't care where. In your luncheon box or under Hooper's pillow. Just somewhere, and within the grounds of this place."
	 				* * * * "Then let him he think he's off the hook.[" ] Make a show of me. And then you'll get your man."
	 					<i>Somehow</i>, I think. But that's the part I need to work.
	 				 -> harris_takes_you_to_hooper

	 			* * * * "Then you'd better get searching[." ]," I reply, tiring of his complaining. A war is a war, you have to expect an enemy. -> its_your_problem

	 			* * *  	"You're right. Let me talk to him[." ], then. As a colleague. Maybe I can get something useful out of him."
	 			 	-> putmein

	 			* * * "You're right." -> shake_head

	 	 * [Block] -> its_your_problem


= harris_being_convinced
	"Makes sense," Harris agrees, cautiously. { evasive > 1:I can see he's still not entirely convinced by my tale, as well he might not be — I've hardly been entirely straight with him.|I can see he's still not certain whether he can trust me.} "Which means the question is, what can we do to rat him out?"
	 	 * [Offer to help] 
	 	 	"Maybe I can help with that."
	 	 	"Oh, yes? And how, exactly?"
	 	 	 * * 	"I'll talk to him." 
	 	 		"What?"
	 	 		"Put me in with Hooper with him. Maybe I can get something useful out of him."
	 	 	 	-> putmein
	 	 	 * * 	"We'll fool him.[" ] He's waiting to be sure that I've been strung up for this, so let's give him what he wants. If he sees me taken away, clapped in irons — he'll go straight to that component and set about getting rid of it."
	 	 	 	-> harris_takes_you_to_hooper

	 	 * [Don't offer to help]
	 	 	I lean back.  -> its_your_problem

= putmein
	Harris shakes his head. 
	"He despises you. I don't see why he'd give himself up to you."
	 * [Insist] "Try me. Just me and him." 
	 	-> go_in_alone
	 * [Give in] "You're right." 
	 	-> shake_head


= shake_head
	// Can't help
	<> I shake my head. "You're right. I don't see how I can help you. So there's only one conclusion."
	"Oh, yes? And what's that?"
	 -> its_your_problem


= its_your_problem
// Won't Help
	"It's your problem. Your security breach. So much for your careful vetting process." 
	I lean back in my chair and fold my arms so the way they shake will not be visible. 
	"You'd better get on with solving it, instead of wasting your time in here with me."
	 -> harrumphs

= harrumphs
	Harris harrumphs. He's thinking it all over.
	 * { putmein  }    	[Wait] 
	 	"All right," he declares, gruffly. "We'll try it. But if this doesn't work, I might just put the both of you in front of a firing squad and be done with these games. Worse things happen in time of war, you know."
	 	"Alone," I add.
	 	 -> go_in_alone

	 * { putmein  }  [Wait] 
	 	"No," Harris declares, finally. "I think you're lying about Hooper. I think you're a clever, scheming young man — that's why we hired you — and you're looking for the only reasonable out this situation has to offer. But I'm not taking it. We know you were in the room with the machine, we know you're of a perverted persuasion, we know you have compromised yourself. There's nothing more to say here. Either you tell me what you've done with that component, or we will hang you and search just as hard. It's your choice."
	 	 -> harris_threatens_lynching



= go_in_alone
	"Alone?"
	"Alone."
	Harris considers it. I watch his eyes, flicking backwards and forwards over mine, like a ribbon—reader loading its program.
	* 	[Patient] "Well?"
	* 	[Impatient] "For God's sake, man, what do you have to lose?" 
	 	~ raise(forceful)
	- 	"We'll be outside the door," Harris replies, seriously. "The first sign of any funny business and we'll have you both on the floor in minutes. You understand? The country needs your brain, but it's not too worried about your legs. Remember that."
		Then he gets to his feet, and opens the door, and marches me out across the yard. The evening is drawing in and there's a chill in the air. My mind is racing. I have one opportunity here — a moment in which to put the fear of God into Hooper and make him do something foolish that places him in harm's way. But how to achieve it?
		"You ready?" Harris demands.
	  * (yes) [Yes]
			"Absolutely."
	  * 	[No]
			"No."
			"Too bad." 
	  * 	[Lie] -> yes

	- 	-> inside_hoopers_hut


/*--------------------------------------------------------------------------------
	Quick visit to see Hooper
--------------------------------------------------------------------------------*/


=== harris_takes_you_to_hooper
	// Past Hooper
	Harris gets to his feet. "All right," he says. "I should no better than to trust a clever man, but we'll give it a go." 
	Then, he smiles, with all his teeth, like a wolf. 
	 { claim_hooper_took_component.hoopers_hut_3:
		"Especially since this is a plan that involves keeping you in handcuffs. I don't see what I have to lose."
	- else:
		"Hooper's in Hut 3 being debriefed by the Captain. Let's see if we can't get his attention somehow."
	}
	// Leading you past Hooper
	He raps on the door for the guard and gives the man a quick instruction. He returns a moment later with a cool pair of iron cuffs. 
	"Put 'em up," Harris instructs, and I do so. The metal closes around my wrists like a trap. I stand and follow Harris willingly out through the door.
	But whatever I'm doing with my body, my mind is scheming. <i>Somehow,</i> I'm thinking, <i>I have to get away from these men long enough to get that component behind Hut 2 and put it somewhere Hooper will go. Or, otherwise, somehow get Hooper to go there himself...</i>
	Harris marches me over to Hut 3, and gestures for the guard to stand aside. Pushing me forward, he opens the door nice and wide. 
	// Hut 3
	"Captain. Manning talked. If you'd step out for a moment?"
	 * 	[Play the part, head down]
	 	From where he's sitting, I know Hooper can see me, so I keep my head down and look guilty as sin. The bastard is probably smiling.
	 	

	 * 	[Look inside the hut]
	 	I look in through the door and catch Hooper's expression. I had half expected him to be smiling be he isn't. He looks shocked, almost hurt. "Iain," he murmurs. "You couldn't..."
	 	 
	 * 	(shouted) [Call to Hooper] 
	 	I have a single moment to shout something to Hooper before the door closes.
	 	"I'll get you Hooper, you'll see!" I cry. Then:
	 	 
	 	 * * "Queen to rook two, checkmate!"[] I call, then laugh viciously, as if I am damning him straight to hell.
	 		~ hooperClueType = CHESS
	 		- - (only_catch) I only catch Hooper's reaction for a moment — his eyebrow lifts in surprise and alarm. Good. If he thinks it is a threat then he just might be careless enough to go looking for what it might mean.
	 	 	 
	 	 * * "Ask not for whom the bell tolls!"
	 	 	He stares back at me, as if were a madman and perhaps for a split second I see him shudder.
	 	 	 
	 	 * * "Two words: messy, without one missing!"[] I cry, laughing. It isn't the best clue, hardly worthy of The Times, but it will have to do.
	 	 		~ hooperClueType = CROSSWORD
	 	 	 -> only_catch

- 	The Captain comes outside, pulling the door to. "What's this?" he asks. "A confession? Just like that?"
	"No," the Commander admits, in a low voice. "I'm afraid not. Rather more a scheme. The idea is to let Hooper go and see what he does. If he believes we have Manning here in irons, he'll try to shift the component."
	"If he has it."
	"Indeed."
	The Captain peers at me for a moment, like I was some kind of curious insect.
	"Sometimes, I think you people are magicians," he remarks. "Other times you seem more like witches. Very well." 
	With that he opens the door to the Hut and goes back inside. The Commander uses the moment to hustle me roughly forward.
	 { shouted  :
		"And what was all that shouting about?" he hisses in my ear as we move towards the barracks. "Are you trying to pull something? Or just make me look incompetent?"
	- else:
		"This scheme of yours had better come off," he hisses in my ear. "Otherwise the Captain is going to start having men tailing <i>me</i> to see where I go on Saturdays."
	}
	* 	[Reassure] 
		{ not shouted :
			"It will. Hooper's running scared," I reply, hoping I sound more confident than I feel.
		- else:
			"Just adding to the drama," I tell him, confidently. "I'm sure you can understand that."
		}
		"I think we've had enough drama today already," Harris replies. "Let's hope for a clean kill."
		
	* 	[Dissuade] 
		{ not shouted:
			"The Captain thought it was a good scheme. You'll most likely get a promotion."
		- else:
			"I'm not trying to do anything except save my neck."
		}
		"Let's hope things work out," Harris agrees darkly.
		
	* 	[Evade] 
		"We're still in ear—shot if they let Hooper go. Best get us inside and then we can talk, if we must."
		"I've had enough of your voice for one day," Harris replies grimly. <>
		
	* 	[Say nothing]
		I let him have his rant. <> 
	- 	He hustles me up the steps of the barracks, keeping me firmly gripped as if I had any chance of giving him, a trained military man, the slip. It's all I can do not to fall into the room.
	  	-> slam_door_shut_and_gone




=== inside_hoopers_hut
	-  	Harris opens the door and pushes me inside. "Captain," he calls. "Could I have a moment?"
		The Captain, looking puzzled, steps out. The door is closed. Hooper stares at me, open—mouthed, about to say something. I probably have less than a minute before the Captain storms back in and declares this plan to be bunkum.
	 	* 	 [Threaten]
	 		"Listen to me, Hooper. We were the only men in that hut today, so we know what happened. But I want you to know this. I put the component inside a breeze—block in the foundations of Hut 2, wrapped in one of your shirts. They're going to find it eventually, and that's going to be what tips the balance. And there's nothing you can do to stop any of that from happening."
	 		~ hooperClueType = STRAIGHT
	 		
	 		His eyes bulge with terror. "What did I do, to you? What did I ever do?"
	 	 	 * * 	[Tell the truth] 
	 	 		"You treated me like vermin. Like something abhorrent."
				"You are something abhorrent."
				"I wasn't. Not when I came here. And I won't be, once you're gone."
				
	 	 	 * * 	[Lie] 
	 	 		"Nothing," I reply. "You're just the other man in the room. One of us has to get the blame."
	 	 	 	
	 	 	 * * 	[Evade] 
	 	 		"It doesn't matter. Just remember what I said. I've beaten you, Hooper. Remember that."
	 		- - 	I get to my feet and open the door of the Hut. The Captain storms back inside and I'm quickly thrown out. 	-> hustled_out


	 * [Bargain] 
	 	 "Hooper, I'll make a deal with you. We both know what happened in that hut this afternoon. I know because I did it, and you know because you know you didn't. But once this is done I'll be rich, and I'll split that with you. I'll let you have the results, too. Your name on the discovery of the Bombe. And it won't hurt the war effort — you know as well as me that the component on its own is worthless, it's the wiring of the Bombe, the usage, that's what's valuable. So how about it?"
	 	Hooper looks back at me, appalled. "You're asking me to commit treason?"
	 	 * * 	[Yes]
	 	 	"Yes, perhaps. But also to ensure your name goes down in the annals of mathematics. -> back_of_hut_2
	 	 * * 	[No] 
	 	 	"No. It's not treason. It's a trade, plain and simple."
	 	 			
	 	 * * 	(lie) [Lie] 
	 	 		"I'm suggesting you save your own skin. I've wrapped that component in one of your shirts, Hooper. They'll be searching this place top to bottom. They'll find it eventually, and when they do, that's the thing that will swing it against you. So take my advice now. Hut 2."
	 	 		 ~ hooperClueType = STRAIGHT

	 	 * * 	[Evade] -> lie
	 	- - 	 -> no_chance

	 	 * [Plead] 
	 		"Please, Hooper. You don't understand. They have information on me.  I don't need to tell you what I've done, you know. Have a soul. And the component — it's nothing. It's not the secret of the Bombe. It's just a part. The German's think it's a weapon — a missile component. Let them have it. Please, man. Just help me."
	 		"Help you?" Hooper stares. "Help you? You're a traitor. A snake in the grass. And you're <i>queer</i>."
	 	 	 * * 	[Deny] 
	 	 		"I'm no traitor. You <i>know</i> I'm not. How much work have I done here against the Germans? I've given my all. And you know as well as I do, if the Reich were to invade, I would be a dead man. Please, Hooper. I'm not doing any of this lightly."
	 	 	 		
	 	 	 * * 	[Accept]
	 	 		"I am what I am," I reply. "I'm the way I was made. But they'll hang me unless you help, Hooper. Don't let them hang me."
	 	 	 		
	 	 	 * * 	[Evade] 
	 	 		"That's not important now. What matters is what you do, this evening."

	 	 	 - - 	"Assuming I wanted to help you," he replies, carefully. "Which I don't. What would I do?"
	 	 		"Nothing. Almost nothing. 
	 	 		-> back_of_hut_2

= back_of_hut_2
	<> All you have to do is go to the back of Hut 2. There's a breeze—block with a cavity. That's where I've put it. I'll be locked up overnight. But you can pick it up and pass it to my contact. He'll be at the south fence around two AM."
	~ hooperClueType = STRAIGHT
	 -> no_chance

= no_chance
	"If you think I'll do that then you're crazy," Hooper replies. 
	At that moment the door flies open and the Captain comes storming back inside.
	 -> hustled_out

= hustled_out
	// To Barracks
	Harris hustles me over to the barracks. "I hope that's the end of it," he mutters.
	"Just be sure to let him out," I reply. "And then see where he goes."
	 -> slam_door_shut_and_gone




/*--------------------------------------------------------------------------------
	Left alone overnight
--------------------------------------------------------------------------------*/


=== slam_door_shut_and_gone
	Then they slam the door shut, and it locks.
	{ hooperClueType == NONE :
		<> How am I supposed to manage anything from in here?
		*   [Try the door] -> try_the_door
		* 	[Try the windows] -> try_the_windows

	- else:
		I can only hope that Hooper bites. If he thinks I'm bitter enough to have framed him, and arrogant enough to have taunted him with {hooperClueType > STRAIGHT:a clue to} where the damning evidence is hidden... 
		If he hates me enough, and is paranoid enough, then he might {hooperClueType > STRAIGHT:unravel my little riddle and} go searching around Hut 2. 
	}

	 * 	[Wait] 	-> night_falls


= try_the_door
	I try the door. It's locked, of course. 

... (file continues)
