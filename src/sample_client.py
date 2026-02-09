import asyncio
from datetime import datetime
import json
import numpy as np
import logging
from pathlib import Path

from load_secrets import username, password
from dc4client.dc_client import DCClient
from dc4client.send_data import TeamModel, MatchNameModel

# ログファイルの保存先ディレクトリを指定
par_dir = Path(__file__).parents[1]
log_dir = par_dir / "logs"

current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_name = f"dc4_{current_time}.log"
log_file_path = log_dir / log_file_name
formatter = logging.Formatter(
    "%(asctime)s, %(name)s : %(levelname)s - %(message)s"
)

async def main():
    # 最初のエンドにおいて、team0が先攻、team1が後攻です。
    # デフォルトではteam1となっており、先攻に切り替えたい場合は下記を
    # team_name=MatchNameModel.team0
    # に変更してください
    json_path = Path(__file__).parents[0] / "match_id.json"

    # match_idの読み込みます。
    with open(json_path, "r") as f:
        match_id = json.load(f)
    client = DCClient(match_id=match_id, username=username, password=password, match_team_name=MatchNameModel.team0)

    # ここで、接続先のサーバのアドレスとポートを指定します。
    # デフォルトではlocalhost:5000となっています。
    # こちらは接続先に応じて変更してください。
    client.set_server_address(host="localhost", port=5000)

    # チーム内の選手情報を取得します。
    with open("team_config.json", "r") as f:
        data = json.load(f)
    client_data = TeamModel(**data)

    # ログ設定(不要であれば削除してください)
    logger = logging.getLogger("client")
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8", mode="w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.info(f"client_data.team_name: {client_data.team_name}")
    logger.debug(f"client_data: {client_data}")


    # チーム情報をサーバに送信します。
    # 相手のクライアントも同様にチーム情報を送信するまで待機します。
    # 送信後、自チームの名前を受け取ります(team0 または team1)。
    # 両チームが揃うと試合が開始され、思考時間のカウントが始まります。
    # そのため、AIの初期化などはこの前に行ってください。
    match_team_name: MatchNameModel = await client.send_team_info(client_data)

    async for state_data in client.receive_state_data():
        # ゲーム終了の判定
        if (winner_team := client.get_winner_team()) is not None:
            logger.info(f"Winner: {winner_team}")
            break
        
        logger.info(f"state_data: {state_data}")

        next_shot_team = client.get_next_team()
        logger.info(f"next_shot_team: {next_shot_team}")

        if next_shot_team == match_team_name:
            # AIを実装する際の処理はこちらになります。
            await asyncio.sleep(2)  # 思考時間
            translational_velocity = 2.33
            angular_velocity = np.pi / 2
            shot_angle = 91.7 * np.pi / 180
            await client.send_shot_info(
                translational_velocity=translational_velocity,
                shot_angle=shot_angle,
                angular_velocity=angular_velocity,
            )
            # なお、デジタルカーリング3で使用されていた、(vx, vy, rotation(cw または ccw))での送信も可能です。
            # vx = 0.0
            # vy = 2.33
            # rotation = "cw"
            # await client.send_shot_info_dc3(
            #     vx=vx,
            #     vy=vy,
            #     rotation=rotation,
            # )

if __name__ == "__main__":
    asyncio.run(main())
