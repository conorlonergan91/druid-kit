"""Example route: Sentinel Hill (18) -> Defias chain -> Deadmines -> Aquatic Form -> south Darkshore (20).

Step fields:
  do     accept | turnin | complete | goto | fly | hearth | train | level | note | fp | home | abandon (qs = [quest ids])
  q      quest ID (verified) ; name = quest title (also used to match when the ID is unsure)
  npc    who to talk to ; where = plain-words place ; goto = [zone, x, y] (verified only)
  to     fly/hearth destination (zone or subzone text); for fp/home the town (fp = learn its flight path,
         home = set the hearthstone there) ; pick = reward to take ; tip = one short line
Check travel with: python3 tools/route_check.py tools/example_route.py --home <save home> --flights "<a;b>"
  text   main line for note/goto/complete steps
"""

W = "Westfall"
SW = "Stormwind City"
RR = "Redridge Mountains"
MG = "Moonglade"
DS = "Darkshore"

GRYAN = {"npc": "Gryan Stoutmantle", "where": "Sentinel Hill tower", "goto": [W, 56.2, 47.6]}


def g(**kw):
    return kw


ROUTE = {
    "id": "v1-2026-11-17",
    "sections": [
        {
            "title": "Westfall: Defias chain (18-19)",
            "steps": [
                g(do="turnin", q=14, name="The People's Militia", pick="Fist of the People's Militia", **GRYAN),
                g(
                    do="note",
                    text="Wear Fist of the People's Militia. Alt+B at a vendor: sell the Torchlight Wand and Hunting Bow.",
                ),
                g(
                    do="accept",
                    q=214,
                    name="Red Silk Bandanas",
                    npc="Scout Riell",
                    where="top of the Sentinel Hill tower",
                    goto=[W, 56.6, 47.4],
                ),
                g(do="fly", to="Stormwind", npc="Thor (flight master)", where="Sentinel Hill", tip="1s 10c."),
                g(
                    do="turnin",
                    q=399,
                    name="Humble Beginnings",
                    npc="Baros Alexston",
                    where="Cathedral Square",
                    goto=[SW, 49.0, 30.2],
                ),
                g(
                    do="note",
                    text="Library books: hand any you carry to Garion Wendell, top of the Wizard's Sanctum, Mage Quarter.",
                    tip="Skip if you'd rather keep it banked for now.",
                ),
                g(
                    do="goto",
                    text="Walk to Lakeshire, Redridge",
                    to="Lakeshire",
                    where="leave by the main gate, follow the road east through Elwynn past Goldshire into Redridge",
                    goto=[RR, 26.0, 46.0],
                ),
                g(
                    do="turnin",
                    q=65,
                    name="The Defias Brotherhood",
                    npc="Wiley the Black",
                    where="upstairs in the Lakeshire inn",
                    goto=[RR, 26.0, 46.0],
                ),
                g(
                    do="accept",
                    q=132,
                    name="The Defias Brotherhood",
                    npc="Wiley the Black",
                    where="upstairs in the Lakeshire inn",
                ),
                g(do="fp", to="Lakeshire", npc="Ariena Stormfeather", where="Lakeshire flight master, by the bridge"),
                g(do="fly", to="Sentinel Hill", where="Lakeshire flight master (via Stormwind)"),
                g(do="turnin", q=132, name="The Defias Brotherhood", **GRYAN),
                g(do="accept", q=135, name="The Defias Brotherhood", **GRYAN),
                g(do="fly", to="Stormwind", where="Sentinel Hill flight master"),
                g(
                    do="turnin",
                    q=135,
                    name="The Defias Brotherhood",
                    npc="Master Mathias Shaw",
                    where="SI:7 building in Old Town, upstairs",
                ),
                g(do="accept", q=141, name="The Defias Brotherhood", npc="Master Mathias Shaw", where="SI:7, Old Town"),
                g(do="fly", to="Sentinel Hill", where="Stormwind flight master"),
                g(do="turnin", q=141, name="The Defias Brotherhood", **GRYAN),
                g(do="accept", q=142, name="The Defias Brotherhood", **GRYAN),
                g(
                    do="complete",
                    q=142,
                    name="The Defias Brotherhood",
                    text="Kill the Defias Messenger for A Mysterious Message",
                    where="he starts by the Moonbrook blacksmith and walks the road north to the Gold Coast Quarry and Jangolode Mine",
                    goto=[W, 44.4, 69.6],
                    tip="He goes inside both mines; wait on the road if you miss him.",
                ),
                g(do="turnin", q=142, name="The Defias Brotherhood", **GRYAN),
                g(
                    do="accept",
                    q=155,
                    name="The Defias Brotherhood",
                    npc="The Defias Traitor",
                    where="in front of the Sentinel Hill tower",
                    goto=[W, 56.2, 47.6],
                ),
                g(
                    do="complete",
                    q=155,
                    name="The Defias Brotherhood",
                    text="Escort the Defias Traitor to the hideout in Moonbrook",
                    tip="Stay close; Defias ambush him on the way. Better with a friend.",
                ),
                g(do="turnin", q=155, name="The Defias Brotherhood", **GRYAN),
                g(
                    do="accept",
                    q=166,
                    name="The Defias Brotherhood",
                    tip="Kill Edwin VanCleef in the Deadmines.",
                    **GRYAN,
                ),
            ],
        },
        {
            "title": "The Deadmines (18-20, group)",
            "steps": [
                g(
                    do="note",
                    text="Find a group: ask friends first, or Looking for Group (green eye): The Deadmines, tick Tank + Damage, List.",
                    tip="Eat for Well Fed and drink an Elixir of Minor Strength before you start.",
                ),
                g(
                    do="goto",
                    text="Deadmines entrance",
                    to="The Deadmines",
                    where="the mine in Moonbrook; follow the tunnel to the portal",
                    goto=[W, 42.0, 72.0],
                ),
                g(
                    do="complete",
                    q=214,
                    name="Red Silk Bandanas",
                    text="Red Silk Bandanas from Defias miners and overseers",
                ),
                g(do="complete", q=168, name="Collecting Memories", text="4 Miners' Union Cards from the miners"),
                g(do="complete", q=167, name="Oh Brother...", text="Thistlenettle's Badge from Foreman Thistlenettle"),
                g(
                    do="complete",
                    q=2040,
                    name="Underground Assault",
                    text="Gnoam Sprecklesprocket from Sneed's Shredder",
                ),
                g(
                    do="complete",
                    q=166,
                    name="The Defias Brotherhood",
                    text="Kill Edwin VanCleef (last boss, on the ship)",
                    tip="Loot An Unsent Letter from him and right-click it to start its quest.",
                ),
            ],
        },
        {
            "title": "Hand-ins: Sentinel Hill and Stormwind",
            "steps": [
                g(
                    do="turnin",
                    q=166,
                    name="The Defias Brotherhood",
                    tip='Say "update" first so I can pick your reward.',
                    **GRYAN,
                ),
                g(
                    do="turnin",
                    q=214,
                    name="Red Silk Bandanas",
                    npc="Scout Riell",
                    where="top of the Sentinel Hill tower",
                    goto=[W, 56.6, 47.4],
                ),
                g(do="fly", to="Stormwind", where="Sentinel Hill flight master"),
                g(
                    do="turnin",
                    q=168,
                    name="Collecting Memories",
                    npc="Wilder Thistlenettle",
                    where="Dwarven District",
                    goto=[SW, 65.2, 21.2],
                    pick="Dusty Mining Gloves",
                ),
                g(
                    do="turnin",
                    q=167,
                    name="Oh Brother...",
                    npc="Wilder Thistlenettle",
                    where="Dwarven District",
                    pick="Miner's Revenge",
                    tip="Sell Miner's Revenge: 17s 75c.",
                ),
                g(
                    do="turnin",
                    q=2040,
                    name="Underground Assault",
                    npc="Shoni the Shilent",
                    where="Dwarven District",
                    goto=[SW, 55.4, 12.4],
                    pick="Bravo's Armbands",
                ),
                g(
                    do="turnin",
                    name="An Unsent Letter",
                    npc="Baros Alexston",
                    where="Cathedral Square",
                    goto=[SW, 49.0, 30.2],
                ),
            ],
        },
        {
            "title": "Moonglade and Darnassus: Aquatic Form",
            "steps": [
                g(do="goto", text="Cast Teleport: Moonglade", to="Moonglade"),
                g(
                    do="train",
                    npc="Loganaar (druid trainer)",
                    where="Nighthaven, Moonglade",
                    tip="Train everything new for your level.",
                ),
                g(
                    do="complete",
                    q=272,
                    name="Trial of the Sea Lion",
                    text="Right-click a pendant half at the Shrine of Remulos to join them into the Pendant of the Sea Lion",
                    goto=[MG, 36.5, 40.1],
                ),
                g(
                    do="turnin",
                    q=272,
                    name="Trial of the Sea Lion",
                    npc="Dendrite Starblaze",
                    where="Nighthaven",
                    goto=[MG, 56.2, 30.7],
                ),
                g(do="accept", name="Aquatic Form", npc="Dendrite Starblaze", where="Nighthaven"),
                g(
                    do="fly",
                    to="Rut'theran Village",
                    where="Nighthaven flight master",
                    tip="Then take the pink portal up to Darnassus.",
                ),
                g(
                    do="turnin",
                    name="Aquatic Form",
                    npc="Mathrengyl Bearwalker",
                    where="Cenarion Enclave, Darnassus",
                    goto=["Darnassus", 35.2, 8.0],
                ),
                g(
                    do="goto",
                    text="Boat to Auberdine",
                    to="Auberdine",
                    where="back down the portal to Rut'theran; the boat leaves from the dock",
                    tip="Free, a few minutes.",
                ),
                g(do="fp", to="Auberdine", npc="Caylais Moonfeather", where="Auberdine flight master"),
                g(
                    do="home",
                    to="Auberdine",
                    npc="Innkeeper Shaussiy",
                    where="Auberdine inn",
                    tip="Darkshore is your base for the next levels.",
                ),
            ],
        },
        {
            "title": "South Darkshore (19-20)",
            "steps": [
                g(do="turnin", q=97926, name="Making Do", npc="Thundris Windweaver", where="Auberdine"),
                g(do="accept", name="Easy Strider Living", npc="Alanndarian Nightsong", where="Auberdine"),
                g(
                    do="complete",
                    q=6123,
                    name="Gathering the Cure",
                    text="12 Lunar Fungus from the caves east of Auberdine",
                    tip="Grey mushrooms with bright blue spots. Pull the moonkin one at a time.",
                ),
                g(
                    do="complete",
                    q=963,
                    name="For Love Eternal",
                    text="Kill Anaya Dawnrunner at the Ameth'Aran ruins for her pendant",
                    goto=[DS, 41.8, 60.7],
                    tip="She hits hard: Bear Form with Rejuvenation on.",
                ),
                g(
                    do="complete",
                    q=986,
                    name="A Lost Master",
                    text="5 Fine Moonstalker Pelts from Moonstalker Sires and Matriarchs",
                    where="along the Wildbend River",
                    tip="Plain Moonstalkers don't drop them.",
                ),
                g(
                    do="complete",
                    name="Easy Strider Living",
                    text="5 Strider Meat from Foreststriders along the southern road",
                ),
                g(
                    do="complete",
                    q=1003,
                    name="Buzzbox 525",
                    text="4 Grizzled Scalps from Grizzled Thistle Bears, then use the Buzzbox",
                    where="far south, between the Grove of the Ancients and Blackwood Den",
                ),
                g(
                    do="complete",
                    q=98025,
                    name="WANTED: Jai'vhanel",
                    text="Kill Jai'vhanel for her feather (Questie's marker)",
                    pick="Darnassian Knife",
                    tip="Sell the knife: 4s 42c.",
                ),
                g(
                    do="complete",
                    q=2139,
                    name="Tharnariun's Hope",
                    text="Kill the Den Mother in her cave near Bashal'Aran",
                    goto=[DS, 52.3, 35.8],
                    tip="Kill her cubs first. Easier with a friend.",
                ),
                g(
                    do="complete",
                    q=947,
                    name="Cave Mushrooms",
                    text="5 Scaber Stalks and a Death Cap in the cave behind Cliffspring Falls",
                    goto=[DS, 54.4, 31.8],
                    tip="Turn right inside for the Death Cap.",
                ),
                g(
                    do="complete",
                    q=4740,
                    name="WANTED: Murkdeep!",
                    text="Clear the murloc camp, stand in the middle: 3 waves, Murkdeep last",
                    goto=[DS, 36.0, 76.0],
                    tip="Stay in Bear Form; heal between waves.",
                ),
                g(do="turnin", q=6123, name="Gathering the Cure", npc="Alanndarian Nightsong", where="Auberdine"),
                g(do="turnin", name="Easy Strider Living", npc="Alanndarian Nightsong", where="Auberdine"),
                g(do="turnin", q=986, name="A Lost Master", npc="Terenthis", where="Auberdine"),
                g(
                    do="turnin",
                    q=2139,
                    name="Tharnariun's Hope",
                    npc="Tharnariun Treetender",
                    where="Auberdine",
                    pick="Timberland Cape",
                ),
                g(
                    do="turnin",
                    q=947,
                    name="Cave Mushrooms",
                    npc="Thundris Windweaver",
                    where="Auberdine",
                    pick="Gustweald Cloak",
                ),
                g(do="turnin", q=4740, name="WANTED: Murkdeep!", npc="Sentinel Glynda Nal'Shea", where="Auberdine"),
                g(do="level", level=20, text='Cat Form! Say "update" for the next part (Wetlands).'),
            ],
        },
    ],
}
