.PHONY: backend frontend test docker clean

backend:
	cd backend && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest
	cd frontend && npm test

docker:
	docker compose up --build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	cd frontend && rm -rf node_modules dist
