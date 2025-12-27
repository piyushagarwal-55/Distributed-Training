import { render, screen } from '@testing-library/react';
import { Card } from '@/components/atoms/Card';

describe('Card Component', () => {
  it('renders children', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('applies variant styles', () => {
    const { container } = render(<Card variant="purple">Content</Card>);
    expect(container.firstChild).toHaveClass('bg-purple-50');
  });

  it('applies custom className', () => {
    const { container } = render(<Card className="custom-class">Content</Card>);
    expect(container.firstChild).toHaveClass('custom-class');
  });
});
