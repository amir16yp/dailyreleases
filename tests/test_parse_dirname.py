import unittest
from datetime import datetime, timedelta

from dailyreleases import parsing
from dailyreleases.parsing import ReleaseType, Platform, ParseError
from dailyreleases.predbs import Pre


class ParseDirnameTestCase(unittest.TestCase):
    def test_single_word_release(self):
        pre = Pre("Aztez-DARKSiDERS", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)

        self.assertEqual("Aztez-DARKSiDERS", r.dirname)
        self.assertEqual("Aztez", r.rls_name)
        self.assertEqual("Aztez", r.game_name)
        self.assertEqual(Platform.WINDOWS, r.platform)
        self.assertEqual(ReleaseType.GAME, r.type)
        self.assertEqual("DARKSiDERS", r.group)
        self.assertIn("store.steampowered.com/app/244750", r.store_links["Steam"])
        self.assertEqual([], r.tags)
        self.assertEqual([], r.highlights)

    def test_error_on_blacklisted_word(self):
        pre = Pre(
            "Anthemion.Software.DialogBlocks.v5.15.LINUX.Incl.Keygen-AMPED",
            "nfo_link",
            datetime.utcnow(),
        )
        with self.assertRaisesRegex(ParseError, "Contains blacklisted word"):
            parsing.parse_pre(pre)

    def test_error_on_old(self):
        pre = Pre(
            "Aztez-DARKSiDERS", "nfo_link", datetime.utcnow() - timedelta(hours=50)
        )
        with self.assertRaisesRegex(ParseError, "Older than 48 hours"):
            parsing.parse_pre(pre)

    def test_error_on_software(self):
        pre = Pre(
            "Tecplot.RS.2017.R1.v1.2.85254.X64-AMPED", "nfo_link", datetime.utcnow()
        )
        with self.assertRaisesRegex(ParseError, "No store link: probably software"):
            parsing.parse_pre(pre)

    def test_nuked_release(self):
        # TODO: Actual nuke handling?
        pre = Pre("Battlefield.1-CPY", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)
        self.assertEqual("Battlefield.1-CPY", r.dirname)

    def test_update(self):
        pre = Pre(
            "Car.Mechanic.Simulator.2018.Plymouth.Update.v1.5.1.Hotfix-PLAZA",
            "nfo_link",
            datetime.utcnow(),
        )
        r = parsing.parse_pre(pre)
        self.assertEqual(ReleaseType.UPDATE, r.type)
        self.assertIn("store.steampowered.com/app/754920", r.store_links["Steam"])

    def test_proper_highlight(self):
        pre = Pre("Death.Coming.PROPER-SiMPLEX", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)
        self.assertEqual(["PROPER"], r.highlights)
        self.assertIn("store.steampowered.com/app/705120", r.store_links["Steam"])

    def test_macos_release(self):
        pre = Pre(
            "The_Fall_Part_2_Unbound_MacOS-Razor1911", "nfo_link", datetime.utcnow()
        )
        r = parsing.parse_pre(pre)
        self.assertEqual(Platform.OSX, r.platform)
        self.assertEqual(ReleaseType.GAME, r.type)
        self.assertIn("store.steampowered.com/app/510490", r.store_links["Steam"])
        self.assertIn("gog.com/en/game/the_fall_part_2_unbound", r.store_links["GOG"])

    def test_macosx_update(self):
        pre = Pre(
            "Cult_of_the_Lamb_v1.1.3_MacOS-Razor1911",
            "nfo_link",
            datetime.utcnow(),
        )
        r = parsing.parse_pre(pre)
        self.assertEqual(Platform.OSX, r.platform)
        self.assertEqual(ReleaseType.UPDATE, r.type)
        self.assertIn("store.steampowered.com/app/1313140", r.store_links["Steam"])
        self.assertIn("gog.com/en/game/cult_of_the_lamb", r.store_links["GOG"])

    def test_linux_release(self):
        pre = Pre(
            "Sphinx_And_The_Cursed_Mummy_Linux-Razor1911", "nfo_link", datetime.utcnow()
        )
        r = parsing.parse_pre(pre)
        self.assertEqual(Platform.LINUX, r.platform)
        self.assertEqual(ReleaseType.GAME, r.type)
        self.assertIn("store.steampowered.com/app/606710", r.store_links["Steam"])
        self.assertIn("gog.com/en/game/sphinx_and_the_cursed_mummy", r.store_links["GOG"])

    def test_dlc_explicit(self):
        pre = Pre("Fallout.4.Far.Harbor.DLC-CODEX", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)
        self.assertIn("store.steampowered.com/app/435881", r.store_links["Steam"])
        self.assertEqual(ReleaseType.DLC, r.type)

    def test_dlc_implicit(self):
        pre = Pre("Euro.Truck.Simulator.2.Italia-CODEX", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)
        self.assertEqual(ReleaseType.DLC, r.type)
        self.assertIn("store.steampowered.com/app/558244", r.store_links["Steam"])

    def test_incl_dlc_update(self):
        pre = Pre(
            "Wolfenstein.II.The.New.Colossus.Update.5.incl.DLC-CODEX",
            "nfo_link",
            datetime.utcnow(),
        )
        r = parsing.parse_pre(pre)
        self.assertEqual(ReleaseType.UPDATE, r.type)
        self.assertIn("store.steampowered.com/app/612880", r.store_links["Steam"])

    def test_incl_dlc_release(self):
        pre = Pre("Mutiny.Incl.DLC-DARKSiDERS", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)
        self.assertEqual(ReleaseType.GAME, r.type)

    def test_score_steam(self):
        pre = Pre("BioShock_Infinite-FLT", "nfo_link", datetime.utcnow())
        r1 = parsing.parse_pre(pre)
        self.assertIn("store.steampowered.com/app/8870", r1.store_links["Steam"])
        pre = Pre("Duke.Nukem.Forever.Complete-PLAZA", "nfo_link", datetime.utcnow())
        r2 = parsing.parse_pre(pre)
        self.assertIn("store.steampowered.com/app/57900", r2.store_links["Steam"])
        self.assertGreater(r1.score, r2.score)

    def test_ea(self):
        pre = Pre("Madden.NFL.21.REPACK-CPY", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)
        self.assertIn(
            "ea.com/games/madden-nfl/madden-nfl-23",
            r.store_links["EA"],
        )
        self.assertEqual(-1, r.score)
        self.assertEqual(-1, r.num_reviews)

    def test_gog_exclusive(self):
        # https://www.gog.com/en/games?tags=only-on-gog
        # TODO: Actually use GOG API (gog.update_info)
        pre = Pre(
            "SimCity.3000.Unlimited.v2.0.0.10.Multilingual-DELiGHT",
            "nfo_link",
            datetime.utcnow(),
        )
        r = parsing.parse_pre(pre)
        self.assertIn("www.gog.com/en/game/simcity_3000", r.store_links["GOG"])
        self.assertEqual(-1, r.score)

    def test_gog_exclusive2(self):
        pre = Pre("Europa.Universalis.II-KaliMaaShaktiDe", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)
        self.assertIn("gog.com/en/game/europa_universalis_ii", r.store_links["GOG"])

    def test_epic_games_exclusive(self):
        pre = Pre("Vampire_The_Masquerade_Swansong-Razor1911", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)
        self.assertIn(
            "store.epicgames.com/en-US/p/vampire-the-masquerade-swansong", r.store_links["Epic Games"]
        )

    def test_score_non_steam(self):
        pre = Pre("Ode.RIP.MULTI12-SiMPLEX", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)
        self.assertEqual(-1, r.score)

    def test_tags(self):
        pre = Pre(
            "The.Curious.Expedition.v1.3.7.1.MULTI.7.RIP-Unleashed",
            "nfo_link",
            datetime.utcnow(),
        )
        r = parsing.parse_pre(pre)
        self.assertIn("store.steampowered.com/app/358130", r.store_links["Steam"])
        self.assertEqual(["MULTI.7", "RIP"], r.tags)

    def test_steam_package(self):
        pre = Pre("Anno.2070.Complete.Edition-FAKE", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)
        self.assertEqual("Anno 2070 Complete Edition", r.game_name)
        self.assertGreaterEqual(
            r.num_reviews, 9354
        )  # make sure we got the right game from the package
        self.assertIn("store.steampowered.com/sub/26683", r.store_links["Steam"])

    def test_steam_package_with_dlc_first(self):
        pre = Pre(
            "The.Witcher.3.Wild.Hunt.Game.of.The.Year.Edition-RELOADED",
            "nfo_link",
            datetime.utcnow(),
        )
        r = parsing.parse_pre(pre)
        self.assertEqual(
            "The Witcher 3: Wild Hunt - Game of the Year Edition", r.game_name
        )
        self.assertEqual(ReleaseType.GAME, r.type)
        self.assertIn("store.steampowered.com/sub/124923", r.store_links["Steam"])

    def test_steam_bundle(self):
        pre = Pre("Valve.Complete.Pack-FAKE", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)
        self.assertEqual("Valve.Complete.Pack-FAKE", r.dirname)
        self.assertEqual("Valve Complete Pack", r.game_name)
        self.assertEqual("Windows", r.platform)
        self.assertEqual(ReleaseType.GAME, r.type)
        self.assertIn("store.steampowered.com/bundle/232", r.store_links["Steam"])

    def test_denuvo_in_steam_eula(self):
        pre = Pre("Deus.Ex.Mankind.Divided-CPY", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)
        self.assertEqual(["DENUVO"], r.highlights)

    def test_denuvo_in_steam_drm_notice(self):
        pre = Pre("Batman.Arkham.Knight-CPY", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)
        self.assertEqual(["DENUVO"], r.highlights)

    def test_episode_release(self):
        pre = Pre(
            "Life.is.Strange.Before.the.Storm.Episode.3-CODEX",
            "nfo_link",
            datetime.utcnow(),
        )
        r = parsing.parse_pre(pre)
        self.assertEqual("Life is Strange: Before the Storm Episode 3", r.game_name)
        self.assertEqual(ReleaseType.DLC, r.type)
        self.assertIn("store.steampowered.com/app/704740", r.store_links["Steam"])

    def test_season_and_episode_release(self):
        pre = Pre(
            "Minecraft.Story.Mode.Season.Two.Episode.5.MacOSX-RELOADED",
            "nfo_link",
            datetime.utcnow(),
        )
        r = parsing.parse_pre(pre)
        self.assertEqual("Minecraft Story Mode Season Two Episode 5", r.game_name)

    def test_build_is_update(self):
        pre = Pre("DUSK.Episode.1.Build.2.6-SKIDROW", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)
        self.assertEqual(ReleaseType.UPDATE, r.type)

    def test_prefer_steam_to_microsoft_store(self):
        pre = Pre("Forgiveness-PLAZA", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre)
        self.assertIn("store.steampowered.com/app/971120", r.store_links["Steam"])

    def test_abbreviated_name(self):
        pre = Pre("R.O.V.E.R.The.Game-HOODLUM", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre, offline=True)
        self.assertEqual("R.O.V.E.R The Game", r.game_name)

    def test_abbreviated_name_splits_single_letter(self):
        pre = Pre("Tick.Tock.A.Tale.for.Two-DARKSiDERS", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre, offline=True)
        self.assertEqual("Tick Tock A Tale for Two", r.game_name)

    def test_abbreviated_name_splits_single_number(self):
        pre = Pre("GTA.5.The.Complete.Edition-TEST", "nfo_link", datetime.utcnow())
        r = parsing.parse_pre(pre, offline=True)
        self.assertEqual("GTA 5 The Complete Edition", r.game_name)


if __name__ == "__main__":
    unittest.main()
