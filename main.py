from jinja2 import Environment, FileSystemLoader, select_autoescape
import json
import yaml
import sys
import os

class Spell:
    def __init__(self, config):
        self.config = JsonClass(config)

    def pre_render(self, renderer):
        renderer.make_dir("Spells")
        renderer.make_dir("Effects")
        renderer.make_dir("Items")
    def render(self, renderer):
        renderer.render(
            "spell.json",
            ["Spells", f"Spell_{self.config.name}.json"],
            name=self.config.name,
            namespace=self.config.namespace,
            class_name=self.config.charge.class_name,
            dll=self.config.dll,
            allow_throw=self.config.charge.throw,
            allow_spray=self.config.charge.spray,
            allow_imbue=self.config.charge.imbue)
        renderer.render(
            "spell_item.json",
            ["Items", f"Item_Spell_Spell{self.config.name}.json"],
            orb_name=self.config.name,
            name=self.config.name)
        renderer.render(
            "spell_charge_effect.json",
            ["Effects", f"Effect_Spell_Spell{self.config.name}Charge.json"],
            name=self.config.name,
            charge_start_sound_address=self.config.charge.effect.charge_start_sound_address,
            charge_loop_sound_address=self.config.charge.effect.charge_loop_sound_address,
            vfx_address=self.config.charge.effect.vfx_address)
        renderer.render(
            "spell_orb.json",
            ["Effects", f"Effect_Spell_SpellOrb{self.config.name}.json"],
            name=self.config.name,
            mesh_color_a=self.config.orb.mesh_color_a,
            mesh_color_b=self.config.orb.mesh_color_b,
            mesh_color_c=self.config.orb.mesh_color_c,
            mesh_color_d=self.config.orb.mesh_color_d,
            rune=self.config.orb.rune,
            select_sound_address=self.config.orb.select_sound_address,
            vfx_address=self.config.orb.vfx_address)
        for merge in self.config.merges:
            merge_name = merge.spell_a + merge.spell_b
            renderer.render(
                "merge_spell.json",
                ["Spells", f"Spell_{merge_name}Merge.json"],
                namespace=self.config.namespace,
                class_name=merge.class_name,
                dll=self.config.dll,
                spell_a=merge.spell_a,
                spell_b=merge.spell_b)
            renderer.render(
                "spell_item.json",
                ["Items", f"Item_Spell_Spell{merge_name}.json"],
                orb_name=self.config.name,
                name=merge_name)

    def container(self):
        return [{
            "referenceID": "Spell" + self.config.name,
            "reference": "Item",
            "customValues": []
        }] + [{
            "referenceID": "Spell" + merge.spell_a + merge.spell_b + "Merge",
            "reference": "Item",
            "customValues": []
        } for merge in self.config.merges]

class JsonClass:
    def __init__(self, d):
        self.attrs = []
        for key, value in d.items():
            self.attrs.append(key)
            if type(value) == dict:
                setattr(self, key, JsonClass(value))
            elif type(value) == list:
                setattr(self, key, [
                    JsonClass(x) if type(x) in [dict, list] else x
                    for x in value
                ])
            else:
                setattr(self, key, value)

    def __repr__(self):
        return json.dumps({
            key: getattr(self, key)
            for key in self.attrs
        })

class Renderer:
    def __init__(self, base_dir, env: Environment):
        self.env = env
        self.base_dir = base_dir

    def make_dir(self, name=""):
        dir_name = os.path.join(self.base_dir, name)
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)

    def render(self, template, output, **kwargs):
        data = env.get_template(template).render(**kwargs)
        with open(os.path.join(self.base_dir, *output), "w") as f:
            f.write(data)

def make_container(stuff, renderer):
    renderer.render(
        "Container_PlayerDefault.json",
        ["Container_PlayerDefault.json"],
        contents=json.dumps([subthing for subthing in thing.container() for thing in stuff]))

if __name__ == "__main__":
    env = Environment(loader=FileSystemLoader("templates"))
    with open(sys.argv[1]) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        things = [
            Spell(x) for x in data
        ]
        renderer = Renderer(sys.argv[2], env)
        renderer.make_dir()
        for thing in things:
            thing.pre_render(renderer)
            thing.render(renderer)
        make_container(things, renderer)
