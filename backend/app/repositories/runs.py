from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import RunModel


class RunRepository:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def create_run(
        self,
        session_id: UUID,
        language: str,
        code: str,
        stdin: str,
        stdout: str,
        stderr: str,
        exit_code: int,
        timed_out: bool,
    ) -> RunModel:
        run = RunModel(
            session_id=session_id,
            language=language,
            code=code,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            timed_out=timed_out,
        )
        self.db_session.add(run)
        await self.db_session.commit()
        await self.db_session.refresh(run)
        return run
