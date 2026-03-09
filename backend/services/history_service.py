from repositories.history_repository import HistoryRepository


class HistoryService:

    def __init__(self):
        self.repo = HistoryRepository()


    def get_tag_history(self, tag_path, start=None, end=None, hours=1.0):
        tag_id = self.repo.get_tag_id_by_path(tag_path)

        if not tag_id:
            raise ValueError("Tag not found")

        rows = self.repo.get_history(tag_id, start, end, hours)

        return [
            {"t": row[0].isoformat(), "v": row[1], "q": row[2]}
            for row in rows
        ]


    def calculate_stats(self, rows):
        if not rows:
            return {}

        values = [row[1] for row in rows]

        import statistics

        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "count": len(values),
            "stddev": statistics.stdev(values) if len(values) > 1 else 0,
            "variance": statistics.variance(values) if len(values) > 1 else 0,
            "sum": sum(values),
            "median": statistics.median(values),
            "range": max(values) - min(values),
        }