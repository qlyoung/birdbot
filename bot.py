import yaml
import discord
import aiohttp
import re
import tempfile
import subprocess
import glob
import shutil
import os
import asyncio
from bs4 import BeautifulSoup
from io import BytesIO
from discord import Embed, EmbedField, Option, SlashCommandOptionType

bot = discord.Bot()


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.slash_command()
async def lookup_bird(
    ctx: discord.ApplicationContext,
    bird_name: Option(
        description='Bird name, e.g. "Tufted Titmouse" or "Dickcissel"',
        max_length=100,
        required=True,
    ),
):
    # If we don't pretend to be curl, sometimes we randomly get 403 responses 🙄
    headers = {"User-Agent": "curl/7.81.0"}
    session = aiohttp.ClientSession(headers=headers)

    call_name = "call.mp3"

    # normalize input
    bird_name_normalized = re.sub(r"\s+", "_", bird_name.strip())
    bird_name_normalized = bird_name_normalized.replace("'", "")

    print(f"Using normalized bird name: {bird_name_normalized}")

    # Fetch webpage
    overview_url = (
        f"https://www.allaboutbirds.org/guide/{bird_name_normalized}/overview"
    )
    range_url = f"https://www.allaboutbirds.org/guide/{bird_name_normalized}/maps-range"

    print(f"Requesting {overview_url}")
    async with session.get(overview_url) as response:
        print(f"Response: {response.status}")
        if response.status != 200:
            await ctx.send_response("Couldn't find that bird", ephemeral=True)
            await session.close()
            return

        soup = BeautifulSoup(await response.text(), features="html.parser")
        if "Search Results" in soup.text:
            await ctx.send_response("Couldn't find that bird", ephemeral=True)
            await session.close()
            return

    # Extract data 😎
    bird_name_common = soup.find(class_="species-name").text
    bird_formal = soup.find(class_="species-info").em.text
    bird_order = soup.find(class_="additional-info").contents[0].text.split(" ")[1]
    bird_family = soup.find(class_="additional-info").contents[1].text.split(" ")[1]
    bird_description = " ".join(
        [p.text for p in soup.find("h2", class_="overview").parent.find_all("p")]
    )
    quick_facts = {
        c[0].text: c[1].text
        for c in [
            s.contents
            for s in soup.find("ul", class_="LH-menu").find_all(class_="text-label")
        ]
    }
    hero_image_url = (
        soup.find("section", class_="hero-wrap")["data-interchange"]
        .split(",")[-2]
        .strip()[1:]
    )
    range_map_image_url = (
        soup.find("div", class_="narrow-content")
        .a.find("img")["data-interchange"]
        .split(",")[-2]
        .strip()[1:]
    )

    bird = Embed(
        title=bird_name_common,
        description=f"*{bird_formal}*\n\n{bird_description}",
        url=overview_url,
    ).set_image(url=hero_image_url)
    bird.add_field(name="Order", value=bird_order)
    bird.add_field(name="Family", value=bird_family)
    bird.add_field(name="\u200B", value="\u200B", inline=False)
    for fact, value in quick_facts.items():
        bird.add_field(name=fact, value=value)

    bird_range = Embed(title=f"{bird_name_common} - Range", url=range_url).set_image(
        url=range_map_image_url
    )

    await ctx.send_response(embeds=[bird, bird_range])
    await session.close()


@bot.slash_command(description="Send a picture of a bird; the bot will attempt to identify it")
@discord.commands.option("bird_pic", type=SlashCommandOptionType.attachment, description="Picture of bird to identify; NA species only for now", required=True)
async def identify_bird(
    ctx: discord.ApplicationContext,
    bird_pic,
):
    if bird_pic.size > 100000000:
        ctx.send_response("Image too large")

    try:
        shutil.rmtree("yolov5/runs/detect/result")
    except:
        pass

    (bird_file, bird_path) = tempfile.mkstemp()
    bird_path = bird_path + bird_pic.filename
    await bird_pic.save(bird_path)
    await ctx.defer()
    proc = await asyncio.create_subprocess_shell(f"python3 ./yolov5/detect.py --device cpu --weights ./yolobirds/models/nabirds_det_v5m_b32_e300/weights/best.pt --source {bird_path} --name result --save-txt")
    await proc.communicate()
    # os.remove(bird_path)
    labelfiles = glob.glob("yolov5/runs/detect/result/labels/*.txt")
    if len(labelfiles) == 0:
        await ctx.send_followup("No birds identified")
        return
    bird_classes = [line.split()[0] for line in open(labelfiles[0]).read().splitlines()]
    # lol
    bird_class_map = {t[0]:t[1] for t in [(l.split()[0], " ".join(l.split()[1:])) for l in open("./yolobirds/models/nabirds_det_v5m_b32_e300/classes.txt").read().splitlines()]}
    bird_names = ", ".join([bird_class_map[bird_class] for bird_class in bird_classes])
    annotated_pic = discord.File(glob.glob("yolov5/runs/detect/result/*.*")[0])
    await ctx.send_followup(f"Identified {bird_names}", file=annotated_pic)

with open("config.yaml") as config_file:
    config = yaml.safe_load(config_file)

bot.run(config["apikey"])
