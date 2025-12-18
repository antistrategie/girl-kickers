Okay so basically I want to make a whole inhouse scripts for everyone’s weapons so we will have full control on how snappy and fast everyone wields their weapons.

But first I want to define what generally would weapons do:

Signature Weapon - The weapon the Doll is imprinted with. The stats they have with this weapon is exceedingly strong which makes them a step up to the average human (in these case… the Vanilla Rangers).

Their attack types and handling stats will be very quick and snappy. Accuracy wise though, just normal or probably -5% so they need to fly more rounds to kill something. Seeing mods like MTF where they one tap everyone with an AR is boring… I want to see lead fly!

Take note dolls SHOULD NOT borrow each other’s weapons.

Backup Weapons - Would contain mostly pistols but could also include primaries to help round out a member depending on a situation (EG. Allowing Springfield to carry a high ROF smg in missions that are too closed quarters.)

Pistol Backup Weapons will have their attack types and handling stats be similar to Rangers but better, but Primary Backup weapons will have their attack types and handling stats be generally worse than Rangers. Dolls with pistols as their signature weapons instead have worse attack types and handling stats with pistol backup weapons too… incase people would try to have Colphne escape her abysmal 6 shot Curva


Okay so examples? Lets use a Ranger Assaulter Mk18 vs current main patch Klukai’s 416 as a comparison 


Mk 18 Weapon Stats

	<ModifiableParams
			numPellets="1"
			roundsPerMagazine="30"
			closedBolt="1"

			cyclicReload="0"
			reloadTime="1800"
			reloadEmptyTime="2500"
			changeInTime="0"
			changeOutTime="0"
			readyTime="325"
			guardTime="160"

			accuracyStart="200"
			accuracyEnd="200"
			accuracyStartDist="0"
			accuracyEndDist="100"
	/>

416 Weapon Stats

        <ModifiableParams
           			numPellets="1"
           			roundsPerMagazine="30"
            		closedBolt="1"

            		cyclicReload="0"
            		reloadTime="1700"
            		reloadEmptyTime="2400"
            		changeInTime="0"
            		changeOutTime="0"
            		readyTime="340"
            		guardTime="200"

            		accuracyStart="160"
            		accuracyEnd="80"
            		accuracyStartDist="0"
            		accuracyEndDist="60"
        />

Currently right now… the weapon stats of the 416 pales in comparison to the Mk18… and this is a trained human’s weapon mind you. Look particularly at the accuracy start and accuracy end stats… The vanilla weapons are done like that in the massive 200s because the attack types actually modify them greatly. Also that reload time is slow… Girls should really reload fast aside from being androids, there is also the matter that will be discussed below.

Now lets get into the attack types that 416 borrows which interestingly the Mk18 uses as well:


<AttackType name="Rangers_RapidFire" rangeMeters="7"/>	


	<AttackType name="Rangers_RapidFire">
		<ModifiableParams
			minAimTime="350"
			maxAimTime="350"
			roundsPerSecondOverride="7"
			minShots="2"
			maxShots="-1"
			resetTime="300"
			accuracyAdd="-100"
			followupShotAccuracyAdd="20"
			critChanceAdd="0"
		/>
	</AttackType>

<AttackType name="Rangers_RapidFireMed" rangeMeters="18" />

	<AttackType name="Rangers_RapidFireMed">
		<ModifiableParams
			minAimTime="350"
			maxAimTime="600"
			roundsPerSecondOverride="6"
			minShots="2"
			maxShots="4"
			resetTime="150"
			accuracyAdd="0"
			followupShotAccuracyAdd="20"
			critChanceAdd="20"
		/>
	</AttackType>

<AttackType name="Rangers_CarbineAimedFire" rangeMeters="40" />

	<AttackType name="Rangers_CarbineAimedFire">
		<ModifiableParams
			minAimTime="600"
			maxAimTime="900"
			roundsPerSecondOverride="2"
			minShots="1"
			maxShots="2"
			resetTime="200"
			accuracyAdd="-120"
			followupShotAccuracyAdd="10"
			critChanceAdd="10"
		/>
	</AttackType>


<AttackType name="Rangers_CarbineAimedFireXX" rangeMeters="9999" />


	<AttackType name="Rangers_CarbineAimedFireXX">
		<ModifiableParams
			minAimTime="900"
			maxAimTime="900"
			roundsPerSecondOverride="1"
			minShots="1"
			maxShots="1"
			resetTime="200"
			accuracyAdd="-150"
			followupShotAccuracyAdd="20"
			critChanceAdd="-20"
		/>
	</AttackType>

If you can imagine and simulate in your head, currently Klukai would miss a lot if she uses the default Ranger attack types with her current weapon. While the simple fix is to update klukai’s weapon, I am more than willing to spend time programming and testing weapon stats for each of their signature weapons since I love them so much.


Now for the fun stuff finally:

I want to recommend the following Signature Weapon Archetypes to make things more flavored for the T-Dolls!

Assault Rifles: Best at mid range, good at long range and fair short range. Attack Types will be coded to shoot at least a burst of 3 everytime as most cinematics have the girls fire in full auto or burst, never single fire. Seeing lots of lead fly is fun! Their crit chances are abysmally low but climb fast per successive shot.

Pistols: Lowest aim time possible at close range and high aim time at extremely long range. Offense-oriented dolls (Nagant, Ksenia) get higher crit chances per shot (meaning their pistols will take out heads more) and Healing-oriented dolls (Colphne, Florence) get high suppression chance per shot (simulating them shooting bad guys close enough to dissuade them from firing). Pistols also have fast ready and guard times, second to SMGs.

SMGs: Second only to pistols in aim time but have the worst accuracy of all the weapons, SMGs make up for it with the incredible ROF of their weapons that will induce high amounts of suppression at any range, and the fastest ready and guard times, allowing them to weave through their teammates and keeping their weapons ready all the time. Unlike in vanilla, my plan is that their crit chances will be abysmally low but they will unload their SMGs full auto at any range to compensate, eventually the continuous stream of bullets will overcome the enemy’s armor coverage and land lethal hits.

Shotguns: Extreme powerhouses at close range and falters hard at long. Vanilla shotguns rely on the sheer number of pellets to take down armored enemy dudes by having each pellet roll against the armor coverage of the target… eventually some makes its way through and enough will kill, even at long range. My change to this is nearly zero aside from tuning the damage a bit higher at closer ranges and lowering it at longer ranges so hopefully we dont get absurd things like Vepley sniping some dude across the map in two shots.

Sniper Rifles: The opposite of the shotgun. Sniper rifles dont exist in vanilla so I am just going to reference your stuff for Springfield, Makiatto and Nemesis. Basically since most of these snipers are suffering from low ROF and magazine size already, we will give them a substantial buff in accuracy and aim time at close range but will still make their best at long range!

LMGs: Basically heavier assault rifles with the ability to suppress, meaning their aim times are a bit slower and their ready and guard times will be slower as well. Mind that the suppression technique will not be limited to them, as having teams without LMGs such as Groza Squad, DEFY and Zucchero would need one rapid fire weapon to fill for them

Melee weapons dont need much adjustment… Krolik is as fine as it is.


So you noticed no mention of shields yes? Well I have this plan where I will do my best to make new animation sets for specific T-Dolls I see fit for frontlining based from whatever existing official characterization they have in the GFL universe. Take note that unless otherwise mentioned, the shielders will be able to use their Signature Weapons with the shield.

Here are the dolls I see fit to wield shields from every team:

Groza Squad: Groza and Colphne (Colphne being small and no mention of massive strength, gets really crippling penalties with a shield)

Note: (Krolik can't be the shielder because 1 I dont know if i can mesh melee with shields and 2 Krolik’s shield does jackshit ingame, her defenses are very low.)

DEFY: Alva and Voymastina (Alva wont be able to use her AN94 with the shield, Voymastina gets lesser penalties with the shield because she is strong…)

Zucchero: Centaureissi and Springfield (Springfield will not be able to use her springfield with a shield, limiting her to backup pistols)

H.I.D.E. 404: Andoris and Leva (Leva gets to have the shield to help her abysmal ROF weapon to be useful when teamed up with Lenna, Android meanwhile is the tank of the team in universe, always the careful one.)

Elmo CE: Helen and Sabrina (They have shields in universe, and they are not penalized much about it)

Frostfall Squad: Lind and Cheeta (Lind has shields in universe, cheeta would just be backup… cheeta would receive heavy penalties with the shield tho)
