"""Guide window: tab buttons laid out in order without overlap."""

import re

from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
UISpecialFrames={}; SlashCmdList={}; DruidKitDB={}
GetTime=function() return 1 end
C_Timer.NewTicker=function() end
made={}
local base=CreateFrame
CreateFrame=function(k,n,p,t) local f=base(); f.kind=k; f.parent=p; f.w=480
  f.SetSize=function(s,w,h) s.w=w end; f.GetFrameLevel=function() return 1 end; f.GetStringHeight=function() return 10 end; f.GetVerticalScroll=function() return 0 end; f.GetPoint=function() return "CENTER",nil,"CENTER",0,0 end; f.GetWidth=function(s) return s.w end
  f.SetPoint=function(s,a,rel,b,x,y) s.x=x end
  made[#made+1]=f; return f end
""")
L.execute(source("DruidKit/DruidKit_Guide.lua"))
L.execute(source("DruidKit/DruidKit.lua"))
L.execute(r"""
DruidKit_ToggleGuide()
tabs={} for _,f in ipairs(made) do if f.label then tabs[#tabs+1]=string.format("%s x=%.0f w=%.0f",f.label.text,f.x or -1,f.w) end end
""")
for t in L.globals().tabs.values():
    print(t)

from expect import check, done

names = ["Now", "Quests", "Combat", "World", "Crafting", "Help", "Talents", "Dungeons"]
tabs = [t for t in L.globals().tabs.values() if t.split()[0] in names]
xs = [float(re.search(r"x=(-?[\d.]+)", t).group(1)) for t in tabs]
check([t.split()[0] for t in tabs] == names, "one tab button per guide tab, in order", tabs)
check(all(b > a for a, b in zip(xs, xs[1:], strict=False)), "tab buttons laid out left to right without overlap")
done("guide_tabs_test")
