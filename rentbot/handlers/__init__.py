from aiogram import Router

from . import admin, channel, filters, own, post, report, start


def all_routers() -> list[Router]:
    # order matters: `start` handles menu buttons and /cancel in any state, so it goes first
    return [admin.router, start.router, filters.router, post.router, own.router,
            report.router, channel.router]
