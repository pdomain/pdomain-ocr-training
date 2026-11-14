"""Guard against two OpenCV distributions sharing the ``cv2/`` directory."""

from __future__ import annotations

from importlib.metadata import distributions

OPENCV_DISTRIBUTIONS = frozenset(
    {
        "opencv-python",
        "opencv-contrib-python",
        "opencv-python-headless",
        "opencv-contrib-python-headless",
    },
)


def test_only_opencv_python_is_installed() -> None:
    installed = {
        name.lower().replace("_", "-")
        for dist in distributions()
        if (name := dist.metadata["Name"]) is not None
    } & OPENCV_DISTRIBUTIONS

    assert installed == {"opencv-python"}
