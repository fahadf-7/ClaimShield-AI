from PIL import Image, ImageDraw

from app.enums import ModelTask
from app.modules.analysis.adapters import FixtureSegmentationAdapter


def fixture_image() -> Image.Image:
    image = Image.new("RGB", (200, 120), (225, 232, 238))
    draw = ImageDraw.Draw(image)
    draw.rectangle((10, 20, 190, 100), fill=(25, 95, 210))
    draw.ellipse((60, 45, 100, 80), fill=(220, 35, 55))
    return image


def test_separate_fixture_adapters_follow_contract():
    part_adapter = FixtureSegmentationAdapter(ModelTask.PART_SEGMENTATION.value)
    damage_adapter = FixtureSegmentationAdapter(ModelTask.DAMAGE_SEGMENTATION.value)
    parts = part_adapter.predict(fixture_image())
    damages = damage_adapter.predict(fixture_image())

    assert [item.class_name for item in parts] == ["FRONT_BUMPER"]
    assert [item.class_name for item in damages] == ["DENT"]
    assert parts[0].mask.shape == (120, 200)
    assert damages[0].confidence == 0.99
    assert part_adapter.metadata.weights_checksum != damage_adapter.metadata.weights_checksum
    assert part_adapter.metadata.is_experimental is True
