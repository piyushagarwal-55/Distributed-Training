# Contributing to HyperGPU

Thank you for your interest in contributing! 🎉

## Quick Links

- 📖 [README.md](README.md) - Project overview
- 🚀 [SETUP.md](SETUP.md) - Setup instructions
- 📋 [QUICKSTART.txt](QUICKSTART.txt) - Quick reference

---

## Getting Started

### 1. Fork & Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/lnmhacks1.git
cd lnmhacks1
```

### 2. Setup Development Environment

```bash
npm install
npm start
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Adding tests

---

## Development Workflow

### Making Changes

1. **Frontend changes:** Edit files in `frontend/src/`
2. **Backend changes:** Edit files in `python-ml-service/src/`
3. **Smart contracts:** Edit files in `smart-contracts/contracts/`

### Testing Your Changes

```bash
# Start development server
npm start

# Test manually
# - Open http://localhost:3000
# - Check API docs: http://localhost:8000/docs
# - Verify changes work as expected
```

### Code Style

**Python:**
- Follow PEP 8
- Use type hints
- Add docstrings to functions

**TypeScript/React:**
- Use TypeScript for type safety
- Follow React best practices
- Use functional components with hooks

**Commits:**
Use [Conventional Commits](https://www.conventionalcommits.org/):
```bash
feat: add new feature
fix: resolve bug
docs: update documentation
style: format code
refactor: restructure code
test: add tests
chore: update dependencies
```

---

## Project Structure

### Frontend (`frontend/`)

```
src/
├── components/
│   ├── atoms/         # Basic UI elements (Button, Card, Input)
│   ├── molecules/     # Composed components (Table, Chart)
│   └── organisms/     # Complex components (Dashboard, NodeManagement)
├── pages/             # Next.js pages (routes)
├── lib/
│   ├── api.ts        # API client
│   ├── store.ts      # Zustand state management
│   └── websocket.ts  # WebSocket client
└── utils/             # Helper functions
```

### Backend (`python-ml-service/`)

```
src/
├── api/
│   └── rest_server.py    # FastAPI routes
├── core/
│   ├── coordinator.py    # Training coordinator
│   ├── gpu_node.py       # Node management
│   └── metrics_collector.py
├── models/
│   ├── node.py          # Pydantic models
│   └── config.py
└── utils/               # Utilities
```

### Smart Contracts (`smart-contracts/`)

```
contracts/
├── TrainingRegistry.sol
├── ContributionTracker.sol
└── RewardDistributor.sol
scripts/
└── deploy.js
```

---

## Adding New Features

### Backend API Endpoint

1. **Define route in `rest_server.py`:**
```python
@self.app.post("/api/your-endpoint")
async def your_endpoint(request: YourRequest):
    """Endpoint description."""
    try:
        # Your logic here
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

2. **Add model in `models/`:**
```python
class YourRequest(BaseModel):
    field1: str
    field2: int
```

3. **Update API client in `frontend/src/lib/api.ts`:**
```typescript
async yourEndpoint(data: YourData) {
  return this.post('/your-endpoint', data);
}
```

### Frontend Component

1. **Create component:**
```tsx
// frontend/src/components/atoms/YourComponent.tsx
export const YourComponent: React.FC<Props> = ({ ...props }) => {
  return <div>...</div>;
};
```

2. **Use in page:**
```tsx
import { YourComponent } from '@/components/atoms/YourComponent';
```

### State Management

Update store in `frontend/src/lib/store.ts`:

```typescript
interface YourStore {
  data: YourData[];
  fetchData: () => Promise<void>;
}

export const useYourStore = create<YourStore>((set) => ({
  data: [],
  fetchData: async () => {
    const response = await apiClient.yourEndpoint();
    set({ data: response });
  },
}));
```

---

## Submitting Changes

### 1. Commit Your Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

### 2. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 3. Create Pull Request

1. Go to GitHub repository
2. Click "New Pull Request"
3. Select your branch
4. Fill in PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update

## Testing
- [ ] Tested locally
- [ ] All services running
- [ ] No console errors

## Screenshots (if applicable)
Add screenshots
```

---

## Common Tasks

### Adding a New API Endpoint

1. Define in `python-ml-service/src/api/rest_server.py`
2. Add to API client: `frontend/src/lib/api.ts`
3. Use in component or store
4. Test with curl or API docs

### Adding a New Page

1. Create file: `frontend/src/pages/your-page.tsx`
2. Add navigation link in `DashboardLayout.tsx`
3. Test routing

### Updating Node Structure

1. Update backend model: `python-ml-service/src/models/node.py`
2. Update mapper: `frontend/src/lib/store.ts` (mapBackendNode)
3. Update TypeScript types: `frontend/src/types/index.ts`

### Deploying Smart Contract

```bash
cd smart-contracts
npx hardhat run scripts/deploy.js --network monad_testnet
```

Update contract address in `python-ml-service/configs/default.json`

---

## Testing Guidelines

### Manual Testing

Before submitting PR:

1. ✅ Start all services: `npm start`
2. ✅ Test on frontend: http://localhost:3000
3. ✅ Check API: http://localhost:8000/docs
4. ✅ Register test node
5. ✅ Start training
6. ✅ Verify all pages work
7. ✅ Check browser console (F12) - no errors

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# Test your endpoint
curl -X POST http://localhost:8000/api/your-endpoint \
  -H "Content-Type: application/json" \
  -d '{"field": "value"}'
```

---

## Troubleshooting Development

### Backend Changes Not Reflecting

- Backend has hot-reload enabled
- If changes don't appear, restart: `npm run dev:backend`

### Frontend Changes Not Reflecting

- Next.js has hot-reload
- If stuck, clear cache: `Ctrl+Shift+R`
- Restart: `npm run dev:frontend`

### Type Errors

```bash
# Frontend
cd frontend
npm run type-check

# Backend
cd python-ml-service
mypy src/
```

---

## Code Review Process

1. **Automated checks** (when CI/CD setup):
   - Linting
   - Type checking
   - Build success

2. **Manual review:**
   - Code quality
   - Functionality
   - Documentation

3. **Testing:**
   - Reviewer tests changes locally
   - Verifies all endpoints work

4. **Merge:**
   - Once approved, maintainer merges
   - Delete feature branch

---

## Resources

### Documentation

- **FastAPI:** https://fastapi.tiangolo.com/
- **Next.js:** https://nextjs.org/docs
- **Hardhat:** https://hardhat.org/docs
- **Zustand:** https://zustand-demo.pmnd.rs/

### Project Docs

- `docs/PROJECT_ANALYSIS.md` - Architecture details
- `docs/roadmap.md` - Development roadmap
- API docs: http://localhost:8000/docs (when running)

---

## Communication

### Reporting Issues

Use GitHub Issues with:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable

### Feature Requests

Create issue with:
- Feature description
- Use case
- Proposed implementation (optional)

---

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

---

## Questions?

- Check [SETUP.md](SETUP.md) for setup help
- Read [README.md](README.md) for project overview
- Open GitHub issue for specific questions

Thank you for contributing to HyperGPU! 🚀
