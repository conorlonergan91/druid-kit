"""A train step that names no trainer ticks only at a druid trainer, not a weapon master or riding trainer."""

from expect import check, done
from wowenv import runtime, source

L = runtime("map")
L.execute(source("DruidKit/DruidKit_Trainers.lua"))
g = L.globals()
check(g.DruidKit_IsDruidTrainer("Loganaar") is True, "a druid trainer counts", None)
check(g.DruidKit_IsDruidTrainer("Ilyenia Moonfire") is False, "a weapon master doesn't", None)
check(g.DruidKit_IsDruidTrainer("Cyndra Kindwhisper") is False, "a profession trainer doesn't", None)
done("r3_steps_trainer_test")
